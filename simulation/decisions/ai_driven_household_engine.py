from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging
import random

from simulation.models import Order, StockOrder
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.ai.household_ai import HouseholdAI

logger = logging.getLogger(__name__)


class AIDrivenHouseholdDecisionEngine(BaseDecisionEngine):
    """가계의 AI 기반 의사결정을 담당하는 엔진."""

    def __init__(
        self,
        ai_engine: HouseholdAI,
        config_module: Any,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.info(
            "AIDrivenHouseholdDecisionEngine initialized.",
            extra={"tick": 0, "tags": ["init"]},
        )

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Any]: # Returns HouseholdActionVector
        """
        AI 엔진을 사용하여 최적의 전술(Vector)을 결정하고, 그에 따른 주문을 생성한다.
        Architecture V2: Continuous Aggressiveness
        """
        household = context.household
        markets = context.markets
        market_data = context.market_data
        current_time = context.current_time

        if household is None:
            # Fallback action vector for returning if agent is None
            from simulation.schemas import HouseholdActionVector
            return [], HouseholdActionVector()

        agent_data = household.get_agent_data()

        goods_list = list(self.config_module.GOODS.keys())
        
        # 1. AI Decision (Vector Output)
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, market_data, goods_list
        )
        
        orders = []

        # 2. Execution: Consumption Logic (Per Item)
        for item_id in goods_list:
            agg_buy = action_vector.consumption_aggressiveness.get(item_id, 0.5)
            
            good_info = self.config_module.GOODS.get(item_id, {})
            utility_effects = good_info.get("utility_effects", {})
            
            # Improved Valuation: Anchor to Market Price + Urgent Need
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_avg_traded_price", self.config_module.MARKET_PRICE_FALLBACK)
            if not avg_price or avg_price <= 0:
                avg_price = self.config_module.MARKET_PRICE_FALLBACK # Fallback
                
            # Valuation factor: Use the most pressing need satisfied by this good
            max_need_value = 0.0
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv
            
            # Need Factor: if max_need is 50 (medium), factor is 1.0. If 100, factor is 2.0.
            need_factor = self.config_module.NEED_FACTOR_BASE + (max_need_value / self.config_module.NEED_FACTOR_SCALE)
            valuation_modifier = self.config_module.VALUATION_MODIFIER_BASE + (agg_buy * self.config_module.VALUATION_MODIFIER_RANGE)
            
            willingness_to_pay = avg_price * need_factor * valuation_modifier
            
            # 3. Execution: Multi-unit Purchase Logic (Bulk Buying)
            # If need is high (> 70) or agg_buy is very high, buy more units.
            max_q = self.config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY
            
            target_quantity = 1.0
            
            if max_need_value > self.config_module.BULK_BUY_NEED_THRESHOLD:
                target_quantity = max_q
            elif agg_buy > self.config_module.BULK_BUY_AGG_THRESHOLD:
                target_quantity = max(1.0, max_q * self.config_module.BULK_BUY_MODERATE_RATIO) # Moderate panic
            
            # Budget Constraint Check: Don't spend more than 50% of assets on a single item per tick
            # unless survival is critical.
            budget_limit = household.assets * self.config_module.BUDGET_LIMIT_NORMAL_RATIO
            if max_need_value > self.config_module.BUDGET_LIMIT_URGENT_NEED:
                budget_limit = household.assets * self.config_module.BUDGET_LIMIT_URGENT_RATIO # Extreme urgency
            
            if willingness_to_pay * target_quantity > budget_limit:
                # Reduce quantity first
                target_quantity = max(1.0, budget_limit / willingness_to_pay)
                # If still too expensive, reduce WTP? No, just buy less.
                if willingness_to_pay * target_quantity > budget_limit:
                    target_quantity = budget_limit / willingness_to_pay
            
            # Final Sanity Check
            if target_quantity >= self.config_module.MIN_PURCHASE_QUANTITY and willingness_to_pay > 0:
                orders.append(
                    Order(household.id, "BUY", item_id, max(1, int(target_quantity)), willingness_to_pay, item_id)
                )

        # 3. Execution: Labor Logic
        labor_market_info = market_data.get("goods_market", {}).get("labor", {})
        market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
        best_market_offer = labor_market_info.get("best_wage_offer", 0.0)
             
        # Scenario A: Already Employed - Monitor market for better wages
        if household.is_employed:
            # Mobility Lever: AI determines how much of a gap triggers a quit
            agg_mobility = action_vector.job_mobility_aggressiveness
            
            # Threshold: 1.0 (if agg=1.0) to 2.0 (if agg=0.0)
            quit_threshold = self.config_module.JOB_QUIT_THRESHOLD_BASE - agg_mobility
            
            # 1. Quitting if market metrics exceed the threshold
            if (market_avg_wage > household.current_wage * quit_threshold or 
                best_market_offer > household.current_wage * quit_threshold):
                
                # Probability scales with mobility intent
                if random.random() < (self.config_module.JOB_QUIT_PROB_BASE + agg_mobility * self.config_module.JOB_QUIT_PROB_SCALE):
                    # print(f"DEBUG: Household {household.id} quitting (AI decision). Current: {household.current_wage:.2f}, Threshold: {quit_threshold:.2f}, BestOffer: {best_market_offer:.2f}")
                    household.quit()

        # Scenario B: Unemployed (Default or just quit) - Always look for work
        if not household.is_employed:
            agg_work = action_vector.work_aggressiveness
            # Reservation Wage logic: more aggressive workers accept lower wages
            reservation_modifier = self.config_module.RESERVATION_WAGE_BASE - (agg_work * self.config_module.RESERVATION_WAGE_RANGE) # Range [0.5, 1.5]
            reservation_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, market_avg_wage * reservation_modifier)

            orders.append(
                Order(household.id, "SELL", "labor", 1, reservation_wage, "labor")
            )

        # ---------------------------------------------------------
        # 4. Execution: Stock Investment Logic
        # ---------------------------------------------------------
        stock_orders = self._make_stock_investment_decisions(
            household, markets, market_data, action_vector, current_time
        )
        # StockOrder는 별도 리스트로 반환 (Order와 다른 타입)
        # 현재는 주식 주문을 markets에 직접 제출
        stock_market = markets.get("stock_market")
        if stock_market is not None:
            for stock_order in stock_orders:
                stock_market.place_order(stock_order, current_time)

        return orders, action_vector

    def _make_stock_investment_decisions(
        self,
        household: "Household",
        markets: Dict[str, Any],
        market_data: Dict[str, Any],
        action_vector: Any,
        current_time: int,
    ) -> List[StockOrder]:
        """
        주식 투자 의사결정을 수행합니다.
        
        투자 적극성(investment_aggressiveness)에 따라:
        - 보유 주식의 매도 여부
        - 신규 주식의 매수 여부
        """
        stock_orders: List[StockOrder] = []
        
        # 주식 시장 활성화 확인
        if not getattr(self.config_module, "STOCK_MARKET_ENABLED", False):
            return stock_orders
        
        stock_market = markets.get("stock_market")
        if stock_market is None:
            return stock_orders
        
        # 투자 가능 여부 확인
        min_assets = getattr(self.config_module, "HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT", 500.0)
        if household.assets < min_assets:
            return stock_orders
        
        agg_invest = action_vector.investment_aggressiveness
        
        # 투자 예산 계산
        budget_ratio = getattr(self.config_module, "HOUSEHOLD_INVESTMENT_BUDGET_RATIO", 0.2)
        investment_budget = household.assets * budget_ratio * agg_invest
        
        # ---------------------------------------------------------
        # A. 매도 결정: 보유 주식 평가
        # ---------------------------------------------------------
        sell_threshold = getattr(self.config_module, "STOCK_SELL_PROFIT_THRESHOLD", 0.15)
        
        for firm_id, shares_owned in list(household.shares_owned.items()):
            if shares_owned <= 0:
                continue
                
            current_price = stock_market.get_stock_price(firm_id)
            if current_price is None:
                continue
            
            # 매도 조건: 투자 적극성이 낮을수록 더 쉽게 매도
            # 또는 주가가 크게 상승한 경우 (이익 실현)
            ref_price = stock_market.reference_prices.get(firm_id, current_price)
            
            # 순자산가치 대비 20% 이상 상승 시 매도 고려
            if current_price > ref_price * (1 + sell_threshold):
                # 투자 적극성이 낮을수록 더 적극적으로 매도
                sell_prob = 0.3 * (1 - agg_invest)
                if random.random() < sell_prob:
                    sell_quantity = min(shares_owned, max(1.0, shares_owned * 0.5))
                    stock_orders.append(
                        StockOrder(
                            agent_id=household.id,
                            order_type="SELL",
                            firm_id=firm_id,
                            quantity=sell_quantity,
                            price=current_price * 0.98,  # 시장가 약간 아래
                        )
                    )
        
        # ---------------------------------------------------------
        # B. 매수 결정: 저평가된 주식 탐색
        # ---------------------------------------------------------
        if investment_budget < getattr(self.config_module, "STOCK_MIN_ORDER_QUANTITY", 1.0) * 10:
            return stock_orders  # 예산 부족
        
        buy_discount = getattr(self.config_module, "STOCK_BUY_DISCOUNT_THRESHOLD", 0.10)
        
        # 모든 기업의 주가 확인
        for firm_id, ref_price in stock_market.reference_prices.items():
            if ref_price <= 0:
                continue
                
            current_price = stock_market.get_stock_price(firm_id) or ref_price
            
            # 매수 조건: 시장가가 순자산가치보다 낮은 경우
            if current_price < ref_price * (1 - buy_discount):
                # 투자 적극성에 비례하여 매수 확률
                buy_prob = 0.2 * agg_invest
                if random.random() < buy_prob:
                    # 예산 내에서 매수 수량 결정
                    max_quantity = investment_budget / current_price
                    buy_quantity = max(1.0, min(10.0, max_quantity * 0.5))
                    
                    if buy_quantity >= 1.0:
                        stock_orders.append(
                            StockOrder(
                                agent_id=household.id,
                                order_type="BUY",
                                firm_id=firm_id,
                                quantity=buy_quantity,
                                price=current_price * 1.02,  # 시장가 약간 위
                            )
                        )
                        # 예산 차감 (실제 거래는 매칭 후 처리)
                        investment_budget -= buy_quantity * current_price
                        
                        if investment_budget <= 0:
                            break
        
        return stock_orders

    # Legacy helper methods removed
    def _execute_tactic(self, *args): return []
    def _handle_specific_purchase(self, *args): return []
