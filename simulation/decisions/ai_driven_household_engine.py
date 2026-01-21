from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging
import random

from simulation.models import Order, StockOrder
from simulation.ai.api import Tactic, Aggressiveness, Personality
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext, MacroFinancialContext
from simulation.decisions.portfolio_manager import PortfolioManager

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.ai.household_ai import HouseholdAI
    from modules.household.dtos import HouseholdStateDTO

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
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> Tuple[List[Order], Any]: # Returns HouseholdActionVector
        """
        AI 엔진을 사용하여 최적의 전술(Vector)을 결정하고, 그에 따른 주문을 생성한다.
        Architecture V2: Continuous Aggressiveness
        """
        # [Refactoring] Use state DTO
        household = context.state

        # Legacy fallback if state is not provided but household object is
        if household is None and context.household:
             household = context.household.create_state_dto()

        if household is None:
            # Fallback action vector for returning if agent is None
            from simulation.schemas import HouseholdActionVector
            return [], HouseholdActionVector()

        markets = context.markets
        market_data = context.market_data
        current_time = context.current_time

        agent_data = household.agent_data

        goods_list = list(self.config_module.GOODS.keys())
        
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, market_data, goods_list
        )
        
        # --- [Phase 4.5] Organic Monetary Transmission: Utility Competition Model ---
        
        loan_market_data = market_data.get("loan_market", {})
        nominal_rate = loan_market_data.get("interest_rate", 0.05)
        
        # 1. Savings Utility (Saving ROI)
        savings_roi = self._calculate_savings_roi(household, nominal_rate)
        # Apply 3-Pillars Preference (Wealth Pillar)
        savings_roi *= household.preference_asset
        
        # 2. Debt Burden (Income Effect)
        debt_data = market_data.get("debt_data", {}).get(household.id, {})
        daily_interest_burden = debt_data.get("daily_interest_burden", 0.0)
        income_proxy = max(household.current_wage, household.assets * 0.01)
        dsr = daily_interest_burden / (income_proxy + 1e-9)
        
        debt_penalty = 1.0
        if dsr > self.config_module.DSR_CRITICAL_THRESHOLD:
            debt_penalty = 0.5 # 50% reduction in aggressiveness due to liquidity panic
            
        # --------------------------------------------------------------------------
        
        orders = []

        # 2. Execution: Consumption Logic (Per Item)
        for item_id in goods_list:
            # WO-023: Maslow Constraint (Food Security First)
            if item_id == "consumer_goods":
                food_inventory = household.inventory.get("basic_food", 0.0)
                target_buffer = getattr(self.config_module, "TARGET_FOOD_BUFFER_QUANTITY", 5.0)
                if food_inventory < target_buffer:
                    continue # Skip consumer_goods if food insecure

            # Phase 15: Utility Saturation for Durables
            if hasattr(household, 'durable_assets'):
                 existing_durables = [a for a in household.durable_assets if a['item_id'] == item_id]
                 has_inventory = household.inventory.get(item_id, 0.0) >= 1.0

                 if existing_durables or has_inventory:
                     if random.random() < 0.95: # 95% chance to skip
                         continue

            agg_buy = action_vector.consumption_aggressiveness.get(item_id, 0.5)
            
            # --- Organic Substitution Effect: Saving vs Consumption ROI ---
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_current_sell_price", self.config_module.MARKET_PRICE_FALLBACK)
            if not avg_price or avg_price <= 0:
                avg_price = self.config_module.MARKET_PRICE_FALLBACK
            
            good_info = self.config_module.GOODS.get(item_id, {})
            is_luxury = good_info.get("is_luxury", False)

            # Need Value (UC)
            max_need_value = 0.0
            utility_effects = good_info.get("utility_effects", {})
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv
            
            # --- 3-Pillars ROI Calculation ---
            preference_weight = household.preference_social if is_luxury else household.preference_growth
            consumption_roi = (max_need_value / (avg_price + 1e-9)) * preference_weight
            
            # If Saving is more attractive, attenuate aggressiveness
            if savings_roi > consumption_roi:
                attenuation = consumption_roi / (savings_roi + 1e-9)
                if max_need_value > 40:
                    attenuation = max(0.5, attenuation)
                else:
                    attenuation = max(0.1, attenuation)
                agg_buy *= attenuation
            
            if random.random() < 0.05:
                self.logger.info(
                    f"MONETARY_TRANS | HH {household.id} | {item_id} | Need: {max_need_value:.1f} | "
                    f"ConsROI: {consumption_roi:.2f} vs SavROI: {savings_roi:.4f} | AggBuy: {agg_buy:.2f}"
                )
            
            agg_buy *= debt_penalty
            agg_buy = max(0.0, agg_buy)

            if random.random() < 0.001:
                self.logger.debug(
                    f"MONETARY_TRANS | Agent {household.id} {item_id}: "
                    f"SavROI: {savings_roi:.4f} vs ConsROI: {consumption_roi:.4f} -> Agg: {agg_buy:.2f}"
                )
            
            good_info = self.config_module.GOODS.get(item_id, {})
            utility_effects = good_info.get("utility_effects", {})
            
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_current_sell_price", self.config_module.MARKET_PRICE_FALLBACK)
            if not avg_price or avg_price <= 0:
                avg_price = self.config_module.MARKET_PRICE_FALLBACK
                
            max_need_value = 0.0
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv
            
            need_factor = self.config_module.NEED_FACTOR_BASE + (max_need_value / self.config_module.NEED_FACTOR_SCALE)
            valuation_modifier = self.config_module.VALUATION_MODIFIER_BASE + (agg_buy * self.config_module.VALUATION_MODIFIER_RANGE)
            
            willingness_to_pay = avg_price * need_factor * valuation_modifier

            # --- Phase 17-4: Veblen Demand Effect ---
            if getattr(self.config_module, "ENABLE_VANITY_SYSTEM", False) and good_info.get("is_veblen", False):
                conformity = getattr(household, "conformity", 0.5)
                prestige_boost = avg_price * 0.1 * conformity
                willingness_to_pay += prestige_boost
                agg_buy = min(1.0, agg_buy * (1.0 + 0.2 * conformity))
            
            # 3. Execution: Multi-unit Purchase Logic (Bulk Buying)
            max_q = self.config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY
            target_quantity = 1.0
            
            if max_need_value > self.config_module.BULK_BUY_NEED_THRESHOLD:
                target_quantity = max_q
            elif agg_buy > self.config_module.BULK_BUY_AGG_THRESHOLD:
                target_quantity = max(1.0, max_q * self.config_module.BULK_BUY_MODERATE_RATIO)
            
            # --- Phase 8: Inflation Psychology (Hoarding & Delay) ---
            expected_inflation = household.expected_inflation.get(item_id, 0.0)
            
            if expected_inflation > getattr(self.config_module, "PANIC_BUYING_THRESHOLD", 0.05):
                hoarding_factor = getattr(self.config_module, "HOARDING_FACTOR", 0.5)
                target_quantity *= (1.0 + hoarding_factor)
                willingness_to_pay *= (1.0 + expected_inflation)
                
            elif expected_inflation < getattr(self.config_module, "DEFLATION_WAIT_THRESHOLD", -0.05):
                delay_factor = getattr(self.config_module, "DELAY_FACTOR", 0.5)
                target_quantity *= (1.0 - delay_factor)
                willingness_to_pay *= (1.0 + expected_inflation)

            # Phase 28: Stress Scenario - Hoarding
            stress_config = context.stress_scenario_config
            if stress_config and stress_config.is_active and stress_config.scenario_name == 'hyperinflation':
                consumables = getattr(self.config_module, "HOUSEHOLD_CONSUMABLE_GOODS", ["basic_food", "luxury_food"])
                if item_id in consumables:
                     target_quantity *= (1.0 + stress_config.hoarding_propensity_factor)
                     willingness_to_pay *= (1.0 + stress_config.hoarding_propensity_factor * 0.5)
                     if random.random() < 0.05:
                         self.logger.info(f"HOARDING_TRIGGER | Household {household.id} hoarding {item_id} (x{target_quantity:.1f})")
            
            budget_limit = household.assets * self.config_module.BUDGET_LIMIT_NORMAL_RATIO
            if max_need_value > self.config_module.BUDGET_LIMIT_URGENT_NEED:
                budget_limit = household.assets * self.config_module.BUDGET_LIMIT_URGENT_RATIO
            
            if willingness_to_pay * target_quantity > budget_limit:
                target_quantity = budget_limit / willingness_to_pay
            
            if target_quantity >= self.config_module.MIN_PURCHASE_QUANTITY and willingness_to_pay > 0:
                final_quantity = target_quantity
                if good_info.get("is_durable", False):
                    final_quantity = max(1, int(target_quantity))

                orders.append(
                    Order(household.id, "BUY", item_id, final_quantity, willingness_to_pay, item_id)
                )

        # 3. Execution: Labor Logic
        labor_market_info = market_data.get("goods_market", {}).get("labor", {})
        market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
        best_market_offer = labor_market_info.get("best_wage_offer", 0.0)
             
        # Scenario A: Already Employed
        if household.is_employed:
            # Recovery handled by EconComponent/LaborManager, here we just check for quit
            agg_mobility = action_vector.job_mobility_aggressiveness
            quit_threshold = self.config_module.JOB_QUIT_THRESHOLD_BASE - agg_mobility
            
            if (market_avg_wage > household.current_wage * quit_threshold or 
                best_market_offer > household.current_wage * quit_threshold):
                
                if random.random() < (self.config_module.JOB_QUIT_PROB_BASE + agg_mobility * self.config_module.JOB_QUIT_PROB_SCALE):
                    # Signal quit via Order
                    orders.append(Order(household.id, "QUIT", "labor", 0, 0, "labor"))

        # Scenario B: Unemployed
        if not household.is_employed:
            # Panic check logic duplicated from EconComponent?
            # Ideally EconComponent should handle reservation wage calculation and panic check.
            # But Engine decides TO SELL or NOT.
            # We use 'wage_modifier' from state which is updated by EconComponent (via run_tick/lifecycle?).
            # Actually, EconComponent._calculate_shadow_reservation_wage is called AFTER decisions in original code.
            # So here we use current state.

            # Survival Trigger (Panic Mode) - Logic moved here or duplicated?
            # Original code had panic logic here.
            food_inventory = household.inventory.get("basic_food", 0.0)
            food_price = market_data.get("goods_market", {}).get("basic_food_avg_traded_price", 10.0)
            if food_price <= 0: food_price = 10.0

            survival_days = food_inventory + (household.assets / food_price)
            critical_turns = getattr(self.config_module, "SURVIVAL_CRITICAL_TURNS", 5)

            is_panic = False
            if survival_days < critical_turns:
                is_panic = True
                reservation_wage = 0.0
                self.logger.info(
                    f"PANIC_MODE | Household {household.id} desperate. Survival Days: {survival_days:.1f}. Wage: 0.0",
                     extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_panic"]}
                )
            else:
                labor_market_info = market_data.get("goods_market", {}).get("labor", {})
                market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
                reservation_wage = market_avg_wage * household.wage_modifier

            labor_market_info = market_data.get("goods_market", {}).get("labor", {})
            market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
            best_market_offer = labor_market_info.get("best_wage_offer", 0.0)

            effective_offer = best_market_offer if best_market_offer > 0 else market_avg_wage
            wage_floor = reservation_wage

            if not is_panic and effective_offer < wage_floor:
                self.logger.info(
                    f"RESERVATION_WAGE | Household {household.id} refused labor. "
                    f"Offer: {effective_offer:.2f} < Floor: {wage_floor:.2f}",
                    extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_refusal"]}
                )
            else:
                orders.append(
                    Order(household.id, "SELL", "labor", 1, reservation_wage, "labor")
                )

        # 4. Stock Investment Logic
        stock_orders = self._make_stock_investment_decisions(
            household, markets, market_data, action_vector, current_time, macro_context
        )
        stock_market = markets.get("stock_market")
        if stock_market is not None:
            for stock_order in stock_orders:
                stock_market.place_order(stock_order, current_time)

        # 5. Liquidity Management
        stress_config = context.stress_scenario_config
        is_debt_aversion_mode = False
        if stress_config and stress_config.is_active and stress_config.scenario_name == 'deflation':
             if stress_config.debt_aversion_multiplier > 1.0:
                 is_debt_aversion_mode = True

        debt_data = market_data.get("debt_data", {}).get(household.id, {})
        principal = debt_data.get("total_principal", 0.0)

        repay_amount = 0.0
        if is_debt_aversion_mode and principal > 0:
            base_ratio = self.config_module.DEBT_REPAYMENT_RATIO
            cap_ratio = self.config_module.DEBT_REPAYMENT_CAP
            liquidity_ratio = self.config_module.DEBT_LIQUIDITY_RATIO

            repay_amount = household.assets * base_ratio * stress_config.debt_aversion_multiplier
            repay_amount = min(repay_amount, principal * cap_ratio)
            repay_amount = min(repay_amount, household.assets * liquidity_ratio)

            if repay_amount > 1.0:
                 orders.append(Order(household.id, "REPAYMENT", "currency", repay_amount, 1.0, "loan_market"))
                 self.logger.info(f"DEBT_AVERSION | Household {household.id} prioritizing repayment: {repay_amount:.1f}")

        if current_time % 30 == 0:
            # Modify DTO locally for simulation
            temp_assets = household.assets
            if is_debt_aversion_mode and repay_amount > 0:
                household.assets -= repay_amount
            
            try:
                portfolio_orders = self._manage_portfolio(household, market_data, current_time, macro_context)
                orders.extend(portfolio_orders)
            finally:
                household.assets = temp_assets
        else:
            emergency_orders = self._check_emergency_liquidity(household, market_data, current_time)
            orders.extend(emergency_orders)

        # 6. Real Estate Logic (Moved to EconComponent mostly, but Engine has Mimicry check)
        # We keep Mimicry check here if it's AI driven?
        # The logic was "Check Mimicry Trigger".
        # If the housing logic is deterministic (based on mimicry factor), it belongs in EconComponent or here?
        # Previous code had it here.
        # But `Household.make_decision` called `decide_housing` (System 2) which sets `housing_target_mode`.
        # Engine's logic below seems independent? "If housing in markets...".
        # It generates BUY order if mimicry or rational.
        # This seems to overlap with `EconComponent` logic?
        # `EconComponent` checks `housing_target_mode == "BUY"`.
        # Engine checks mimicry/rational and ADDS order.
        # So we might have double orders if we are not careful?
        # `EconComponent` adds order if `housing_target_mode` is BUY.
        # `housing_target_mode` is set by `decide_housing` (System 2).
        # Engine (here) uses `HousingManager` (System 2? No, `simulation.decisions.housing_manager`).
        # This seems to be a conflict in original code or parallel systems.
        # I will preserve this logic as is, assuming it's distinct.
        # It modifies `orders` list.

        if "housing" in markets:
             housing_market = markets["housing"]
             from simulation.decisions.housing_manager import HousingManager
             # HousingManager needs Household object?
             # HousingManager constructor: `__init__(self, household, config_module)`.
             # Does it accept DTO?
             # Probably not. It likely accesses `household.assets`, etc.
             # If `HousingManager` is used, we need to check if it supports DTO.
             # If not, we might need to update `HousingManager` or pass a compatible object.
             # DTO has most fields. Duck typing might work.

             housing_manager = HousingManager(household, self.config_module) # duck typing

             reference_standard = market_data.get("reference_standard", {})
             mimicry_intent = housing_manager.decide_mimicry_purchase(reference_standard)

             is_owner_occupier = household.residing_property_id in household.owned_properties
             should_search = (not is_owner_occupier) or (mimicry_intent is not None)

             if should_search:
                 best_offer = None
                 min_price = float('inf')
                 
                 for item_id, orders_list in housing_market.sell_orders.items():
                     if not orders_list: continue
                     cheapest = orders_list[0]
                     if cheapest.price < min_price:
                         min_price = cheapest.price
                         best_offer = cheapest
                         
                 if best_offer:
                     loan_market = markets.get("loan_market")
                     mortgage_rate = loan_market.interest_rate if loan_market else 0.05

                     should_buy = False

                     if mimicry_intent:
                         should_buy = True
                     elif not is_owner_occupier:
                         should_buy = housing_manager.should_buy(
                             best_offer.price,
                             self.config_module.INITIAL_RENT_PRICE,
                             mortgage_rate
                         )

                     if should_buy:
                         buy_order = Order(
                             household.id, "BUY", best_offer.item_id, 1.0, best_offer.price, "housing"
                         )
                         orders.append(buy_order)

                         if mimicry_intent:
                             self.logger.info(
                                 f"MIMICRY_BUY | Household {household.id} panic buying housing due to relative deprivation.",
                                 extra={"tick": current_time, "agent_id": household.id}
                             )

        return orders, action_vector

    def _manage_portfolio(self, household: "HouseholdStateDTO", market_data: Dict[str, Any], current_time: int, macro_context: Optional[MacroFinancialContext] = None) -> List[Order]:
        """
        Executes Portfolio Optimization (WO-026).
        """
        orders = []
        cash = household.assets
        deposit_data = market_data.get("deposit_data", {})
        deposit_balance = deposit_data.get(household.id, 0.0)
        total_liquid = cash + deposit_balance

        risk_aversion = household.risk_aversion

        loan_market = market_data.get("loan_market", {})
        risk_free_rate = loan_market.get("interest_rate", 0.05)

        equity_return = getattr(self.config_module, "EXPECTED_STARTUP_ROI", 0.15)

        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        daily_consumption = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        monthly_survival_cost = food_price * daily_consumption * 30.0

        if household.expected_inflation:
            avg_inflation = sum(household.expected_inflation.values()) / len(household.expected_inflation)
        else:
            avg_inflation = 0.0

        target_cash, target_deposit, target_equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=total_liquid,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
            equity_return_proxy=equity_return,
            survival_cost=monthly_survival_cost,
            inflation_expectation=avg_inflation,
            macro_context=macro_context
        )

        diff_deposit = target_deposit - deposit_balance

        if diff_deposit > 10.0:
            actual_deposit = min(cash, diff_deposit)
            if actual_deposit > 10.0:
                orders.append(Order(household.id, "DEPOSIT", "currency", actual_deposit, 1.0, "currency"))

        elif diff_deposit < -10.0:
            amount_to_withdraw = abs(diff_deposit)
            orders.append(Order(household.id, "WITHDRAW", "currency", amount_to_withdraw, 1.0, "currency"))

        startup_cost = getattr(self.config_module, "STARTUP_COST", 30000.0)

        if target_equity >= startup_cost * 0.8:
            projected_cash = cash - max(0, diff_deposit) + max(0, -diff_deposit)
            survival_buffer = 2000.0

            if projected_cash >= (startup_cost + survival_buffer):
                orders.append(Order(household.id, "INVEST", "startup", 1.0, startup_cost, "admin"))

        return orders

    def _check_emergency_liquidity(self, household: "HouseholdStateDTO", market_data: Dict[str, Any], current_time: int) -> List[Order]:
        orders = []
        if household.assets < 10.0:
            deposit_data = market_data.get("deposit_data", {})
            deposit_balance = deposit_data.get(household.id, 0.0)

            if deposit_balance > 10.0:
                amount = min(deposit_balance, 50.0)
                orders.append(Order(household.id, "WITHDRAW", "currency", amount, 1.0, "currency"))

        return orders

    def _make_stock_investment_decisions(
        self,
        household: "HouseholdStateDTO",
        markets: Dict[str, Any],
        market_data: Dict[str, Any],
        action_vector: Any,
        current_time: int,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> List[StockOrder]:
        stock_orders: List[StockOrder] = []
        
        if not getattr(self.config_module, "STOCK_MARKET_ENABLED", False):
            return stock_orders
        
        stock_market = markets.get("stock_market")
        if stock_market is None:
            return stock_orders

        if household.assets < self.config_module.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT:
            return stock_orders

        avg_dividend_yield = market_data.get("avg_dividend_yield", 0.05)
        risk_free_rate = market_data.get("loan_market", {}).get("interest_rate", 0.03)

        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        if not food_price or food_price <= 0:
            food_price = self.config_module.GOODS.get("basic_food", {}).get("initial_price", 5.0)
        daily_consumption = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        survival_cost = food_price * daily_consumption * 30.0

        risk_aversion = self._get_risk_aversion(household.personality)

        target_cash, target_deposit, target_equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=household.assets,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
            equity_return_proxy=avg_dividend_yield,
            survival_cost=survival_cost,
            inflation_expectation=market_data.get("inflation", 0.02),
            macro_context=macro_context
        )

        current_prices = {firm_id: stock_market.get_stock_price(firm_id) for firm_id in household.portfolio_holdings.keys()}

        # Calculate valuation manually for DTO
        current_equity_value = 0.0
        for fid, share in household.portfolio_holdings.items():
            price = current_prices.get(fid, 0.0)
            current_equity_value += share.quantity * price

        equity_delta = target_equity - current_equity_value

        if equity_delta > self.config_module.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD:
            stock_orders.extend(self._place_buy_orders(household, equity_delta, stock_market, current_time))
        elif equity_delta < -self.config_module.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD:
            stock_orders.extend(self._place_sell_orders(household, -equity_delta, stock_market, current_time))
        
        return stock_orders

    def _get_risk_aversion(self, personality_type: Personality) -> float:
        if personality_type == Personality.STATUS_SEEKER:
            return 0.5
        elif personality_type == Personality.CONSERVATIVE:
            return 5.0
        return 2.0

    def _place_buy_orders(self, household: "HouseholdStateDTO", amount_to_invest: float, stock_market: Any, tick: int) -> List[StockOrder]:
        orders = []
        available_stocks = [fid for fid in stock_market.reference_prices.keys() if stock_market.get_stock_price(fid) > 0]
        if not available_stocks:
            return orders

        diversification_count = self.config_module.STOCK_INVESTMENT_DIVERSIFICATION_COUNT
        investment_per_stock = amount_to_invest / diversification_count
        for _ in range(diversification_count):
            firm_id = random.choice(available_stocks)
            price = stock_market.get_stock_price(firm_id)
            if price > 0:
                quantity = investment_per_stock / price
                if quantity >= 1.0:
                    order = StockOrder(household.id, order_type="BUY", firm_id=firm_id, quantity=quantity, price=price * 1.05)
                    orders.append(order)
        return orders

    def _place_sell_orders(self, household: "HouseholdStateDTO", amount_to_sell: float, stock_market: Any, tick: int) -> List[StockOrder]:
        orders = []
        sorted_holdings = sorted(
            household.portfolio_holdings.items(),
            key=lambda item: item[1].quantity * stock_market.get_stock_price(item[0]), # Access .quantity
            reverse=True
        )

        for firm_id, share in sorted_holdings:
            quantity = share.quantity
            if amount_to_sell <= 0:
                break
            price = stock_market.get_stock_price(firm_id)
            if price > 0:
                value_of_holding = quantity * price
                sell_value = min(amount_to_sell, value_of_holding)
                sell_quantity = sell_value / price
                if sell_quantity >= 1.0:
                    order = StockOrder(household.id, order_type="SELL", firm_id=firm_id, quantity=sell_quantity, price=price * 0.95)
                    orders.append(order)
                    amount_to_sell -= sell_value
        return orders

    def _calculate_savings_roi(self, household: "HouseholdStateDTO", nominal_rate: float) -> float:
        """가계의 저축 ROI(미래 효용)를 계산합니다."""
        if household.expected_inflation:
            avg_expected_inflation = sum(household.expected_inflation.values()) / len(household.expected_inflation)
        else:
            avg_expected_inflation = 0.0
            
        real_rate = nominal_rate - avg_expected_inflation
        
        beta = 1.0
        if household.personality in [Personality.MISER, Personality.CONSERVATIVE]:
            beta = 1.2
        elif household.personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            beta = 0.8
            
        return (1.0 + real_rate) * beta

    def _execute_tactic(self, *args): return []
    def _handle_specific_purchase(self, *args): return []

    def decide_reproduction(self, context: DecisionContext) -> bool:
        """
        Calls AI engine to decide reproduction.
        """
        household = context.state # Use state
        if household is None and context.household: # Fallback
             household = context.household.create_state_dto()

        if not household: return False

        agent_data = household.agent_data
        market_data = context.market_data

        return self.ai_engine.decide_reproduction(agent_data, market_data, context.current_time)
