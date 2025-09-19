from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING, Optional
import logging

from simulation.models import Order
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai_model import AIDecisionEngine

if TYPE_CHECKING:
    from simulation.core_agents import Household

class HouseholdDecisionEngine(BaseDecisionEngine):
    """가계의 의사결정 로직을 담당하는 엔진.

    가계의 욕구, 자산, 시장 정보 등을 바탕으로 상품 구매, 노동 공급 등의 의사결정을 수행하며,
    주요 의사결정은 AI 엔진에 위임합니다.
    """
    def __init__(self, goods_market: Any = None, labor_market: Any = None, loan_market: Any = None, ai_engine: AIDecisionEngine = None, logger: Optional[logging.Logger] = None) -> None:
        """HouseholdDecisionEngine을 초기화합니다.

        Args:
            goods_market: 상품 시장 인스턴스.
            labor_market: 노동 시장 인스턴스.
            loan_market: 대출 시장 인스턴스.
            ai_engine (AIDecisionEngine, optional): 의사결정을 위임할 AI 엔진 인스턴스. 기본값은 None.
            logger (logging.Logger, optional): 로깅을 위한 Logger 인스턴스. 기본값은 None.
        """
        super().__init__()
        self.goods_market = goods_market
        self.labor_market = labor_market
        self.loan_market = loan_market # LoanMarket 추가
        self.ai_engine = ai_engine # AI 엔진 추가
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.info("HouseholdDecisionEngine initialized.", extra={'tick': 0, 'tags': ['init']})
        if self.ai_engine:
            self.logger.debug(f"HouseholdDecisionEngine initialized with AI engine: {self.ai_engine.__class__.__name__}", extra={'tick': 0, 'tags': ['init', 'ai']})

    def _calculate_reservation_price(self, household: Household, item_id: str, market_data: Dict[str, Any], current_tick: int) -> float:
        """가계의 현재 상태와 상품 정보를 바탕으로 해당 상품에 대한 지불 의사 가격을 계산합니다.

        다양한 요인(기본 가격, 상품 효용, 가계 욕구 수준, 자산 수준, 인지된 시장 가격, 저장성 등)을 고려하여
        가계가 특정 상품에 대해 지불할 용의가 있는 최대 가격을 결정합니다.

        Args:
            household (Household): 가격을 계산할 가계 에이전트 인스턴스.
            item_id (str): 가격을 계산할 상품의 ID.
            market_data (Dict[str, Any]): 현재 시장 상태를 포함하는 딕셔너리.
            current_tick (int): 현재 시뮬레이션 틱.

        Returns:
            float: 계산된 지불 의사 가격.
        """
        import config
        goods_data = market_data["goods_data"]

        log_extra = {'tick': current_tick, 'agent_id': household.id, 'item_id': item_id, 'tags': ['res_price']}

        # 1. 기본 가격 설정
        base_price = config.HOUSEHOLD_RESERVATION_PRICE_BASE
        reservation_price = base_price
        self.logger.debug(f"Item: {item_id}, Step 1 (Base): {reservation_price:.2f}", extra={**log_extra, 'step': 1, 'price': reservation_price})

        # 2. 상품의 효용(utility) 반영
        good_info = next((g for g in goods_data if g['id'] == item_id), None)
        utility_bonus = 0
        if good_info and 'utility_per_need' in good_info:
            total_utility = sum(good_info['utility_per_need'].values())
            utility_bonus = total_utility * config.HOUSEHOLD_NEED_PRICE_MULTIPLIER
            reservation_price += utility_bonus
        self.logger.debug(f"Item: {item_id}, Step 2 (Utility Bonus): {utility_bonus:.2f}, Total: {reservation_price:.2f}", extra={**log_extra, 'step': 2, 'bonus': utility_bonus, 'total_price': reservation_price})

        # 3. 가계의 욕구 수준 반영 (해당 상품이 충족시키는 욕구)
        needs_bonus = 0
        if good_info and 'utility_per_need' in good_info:
            for need_type, utility_value in good_info['utility_per_need'].items():
                if need_type in household.needs:
                    need_component = household.needs[need_type] * utility_value * config.HOUSEHOLD_NEED_PRICE_MULTIPLIER
                    if item_id == 'food' and need_type == 'survival_need' and household.needs[need_type] > config.SURVIVAL_NEED_THRESHOLD:
                        need_component *= 2.0
                    needs_bonus += need_component
            reservation_price += needs_bonus
        self.logger.debug(f"Item: {item_id}, Step 3 (Needs Bonus): {needs_bonus:.2f}, Total: {reservation_price:.2f}", extra={**log_extra, 'step': 3, 'bonus': needs_bonus, 'total_price': reservation_price})

        # 4. 가계의 자산 수준 반영 (필수재에 대한 보정 포함)
        asset_bonus = household.assets * config.HOUSEHOLD_ASSET_PRICE_MULTIPLIER

        # --- GEMINI_PROPOSED_CHANGE_START: 필수재 및 생존 욕구에 따른 자산 보너스 보정 ---
        is_essential = good_info.get('is_essential', False) if good_info else False
        survival_need = household.needs.get('survival_need', 0)

        # 만약 상품이 필수재이고 생존 욕구가 높다면
        if is_essential and survival_need > config.SURVIVAL_NEED_THRESHOLD:
            # 자산이 적더라도 최소한의 구매력을 보장하는 '생존 프리미엄'을 추가
            # 이 프리미엄은 생존 욕구에 비례하여, 기본 가격의 일정 비율만큼 설정
            survival_premium = (survival_need / 100.0) * config.HOUSEHOLD_RESERVATION_PRICE_BASE
            # 기존 자산 보너스와 생존 프리미엄 중 더 큰 값을 선택하여 가격 하한선 보장
            if asset_bonus < survival_premium:
                self.logger.debug(f"Applying survival premium. Original Asset Bonus: {asset_bonus:.2f}, Survival Premium: {survival_premium:.2f}", extra=log_extra)
                asset_bonus = survival_premium
        # --- GEMINI_PROPOSED_CHANGE_END ---

        reservation_price += asset_bonus
        self.logger.debug(f"Item: {item_id}, Step 4 (Asset Bonus): {asset_bonus:.2f}, Total: {reservation_price:.2f}", extra={**log_extra, 'step': 4, 'bonus': asset_bonus, 'total_price': reservation_price})

        # 5. 인지된 시장 가격 반영
        perceived_price = household.perceived_avg_prices.get(item_id, config.GOODS_MARKET_SELL_PRICE)
        price_advantage_bonus = 0
        if reservation_price > perceived_price and perceived_price > 0:
            price_advantage_ratio = (reservation_price - perceived_price) / reservation_price
            price_advantage_bonus = price_advantage_ratio * config.HOUSEHOLD_PRICE_ELASTICITY_FACTOR * reservation_price
            reservation_price += price_advantage_bonus
        self.logger.debug(f"Item: {item_id}, Step 5 (Price Advantage Bonus): {price_advantage_bonus:.2f}, Total: {reservation_price:.2f}", extra={**log_extra, 'step': 5, 'bonus': price_advantage_bonus, 'total_price': reservation_price})

        # 6. 저장성(storability) 반영
        storability = good_info.get('storability', 0.0) if good_info else 0.0
        stockpiling_bonus = 0
        if storability > 0 and perceived_price > 0:
            current_inventory = household.inventory.get(item_id, 0)
            target_inventory = 10.0
            stockpiling_incentive = (target_inventory - current_inventory) / target_inventory * storability
            stockpiling_bonus = max(0, stockpiling_incentive) * config.HOUSEHOLD_STOCKPILING_BONUS_FACTOR * reservation_price
            reservation_price += stockpiling_bonus
        self.logger.debug(f"Item: {item_id}, Step 6 (Stockpiling Bonus): {stockpiling_bonus:.2f}, Total: {reservation_price:.2f}", extra={**log_extra, 'step': 6, 'bonus': stockpiling_bonus, 'total_price': reservation_price})

        final_price = max(config.MIN_SELL_PRICE, reservation_price)
        self.logger.info(f"Item: {item_id}, Final Reservation Price: {final_price:.2f}", extra={**log_extra, 'final_price': final_price})
        return final_price

    def _allocate_budget(self, household: Household, current_tick: int) -> Dict[str, float]:
        """가계의 현재 상태에 따라 소비 예산과 보유 현금을 할당합니다.

        가계의 유동성 욕구(liquidity_need)를 고려하여 자산 중 얼마를 현금으로 보유하고,
        나머지를 소비 예산으로 사용할지 결정합니다.

        Args:
            household (Household): 예산을 할당할 가계 에이전트 인스턴스.
            current_tick (int): 현재 시뮬레이션 틱.

        Returns:
            Dict[str, float]: 소비 예산('consumption_budget')과 보유 현금('cash_to_hold')을 포함하는 딕셔너리.
        """
        import config
        
        liquidity_need = household.needs.get("liquidity_need", 0)
        
        liquidity_ratio = min(config.LIQUIDITY_RATIO_MAX, max(config.LIQUIDITY_RATIO_MIN, liquidity_need / config.LIQUIDITY_RATIO_DIVISOR))
        
        cash_to_hold = household.assets * liquidity_ratio
        consumption_budget = household.assets - cash_to_hold
        
        self.logger.info(
            f"Budget allocated. Total Assets: {household.assets:.2f}, Consumption Budget: {consumption_budget:.2f}, Cash to Hold: {cash_to_hold:.2f}",
            extra={
                'tick': current_tick,
                'agent_id': household.id,
                'tags': ['budget'],
                'total_assets': household.assets,
                'consumption_budget': consumption_budget,
                'cash_to_hold': cash_to_hold,
                'liquidity_ratio': liquidity_ratio
            }
        )
        
        return {
            "consumption_budget": consumption_budget,
            "cash_to_hold": cash_to_hold
        }

    def make_decisions(self, household: Household, current_tick: int, market_data: Dict[str, Any]) -> List[Order]:
        """가계의 의사결정을 수행합니다. 생존 욕구가 높을 경우 규칙 기반으로 식량을 구매하고,
        그 외의 경우에는 AI 엔진에 의사결정을 위임합니다.

        Args:
            household (Household): 의사결정을 수행할 가계 에이전트 인스턴스.
            current_tick (int): 현재 시뮬레이션 틱.
            market_data (Dict[str, Any]): 현재 시장 상태를 포함하는 딕셔너리.

        Returns:
            List[Order]: 생성된 주문(Order) 객체들의 리스트.
        """
        import config
        log_extra = {'tick': current_tick, 'agent_id': household.id, 'tags': ['household_decision']}
        orders = []

        # 1. 생존 욕구 기반의 규칙 기반 식량 구매
        if household.needs.get("survival_need", 0) > config.SURVIVAL_NEED_THRESHOLD:
            self.logger.info(f"Survival need is high ({household.needs['survival_need']:.2f}). Triggering rule-based food purchase.", extra=log_extra)
            
            budget_info = self._allocate_budget(household, current_tick)
            consumption_budget = budget_info["consumption_budget"]

            if consumption_budget > 0:
                reservation_price = self._calculate_reservation_price(household, 'food', market_data, current_tick)
                
                # 시장 가격 확인 (호가가 없으면 기본 가격 사용)
                best_ask = market_data.get('goods_market', {}).get('food_best_ask')
                market_price = best_ask if best_ask is not None else config.GOODS_MARKET_SELL_PRICE

                # 구매 결정: 지불 의사 가격이 시장 가격보다 높거나 같아야 함
                if reservation_price >= market_price:
                    # 구매할 수량 결정 (예산 내에서 최대로)
                    quantity_to_buy = consumption_budget / reservation_price
                    
                    if quantity_to_buy > 0:
                        order = Order(
                            order_type="BUY",
                            agent_id=household.id,
                            item_id="food",
                            quantity=quantity_to_buy,
                            price=reservation_price,
                            market_id='goods_market'
                        )
                        orders.append(order)
                        self.logger.info(f"Generated rule-based BUY order for food. Qty: {quantity_to_buy:.2f}, Price: {reservation_price:.2f}", extra=log_extra)
                else:
                    self.logger.info(f"Skipping food purchase. Reservation price ({reservation_price:.2f}) is lower than market price ({market_price:.2f}).", extra=log_extra)
            else:
                self.logger.warning("No consumption budget to buy food despite high survival need.", extra=log_extra)

        # 2. 노동 공급 결정 (실업 상태일 경우 항상)
        if household.is_active and not household.is_employed:
            self.logger.info(f"Unemployed and seeking work. Creating SELL order for labor.", extra=log_extra)
            
            avg_food_price = market_data.get('food_avg_price', config.GOODS_MARKET_SELL_PRICE)
            reservation_wage = config.BASE_WAGE + (avg_food_price * config.WAGE_INFLATION_ADJUSTMENT_FACTOR)
            
            order = Order(
                order_type="SELL",
                agent_id=household.id,
                item_id="labor",
                quantity=1.0, # Households sell 1 unit of labor
                price=reservation_wage,
                market_id='labor_market'
            )
            orders.append(order)
            self.logger.info(f"Generated rule-based SELL order for labor. Qty: 1.0, Price: {reservation_wage:.2f}", extra=log_extra)

        # 3. AI 기반 의사결정 (규칙 기반 로직이 실행되지 않았을 경우)
        if not orders and self.ai_engine:
            self.logger.debug("Survival need not critical. Delegating to AI engine.", extra=log_extra)
            ai_orders = self.ai_engine.make_decisions(household, market_data, current_tick)
            orders.extend(ai_orders)
        
        return orders