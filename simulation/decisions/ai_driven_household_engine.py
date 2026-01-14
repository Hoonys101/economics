from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging
import random

from simulation.models import Order, StockOrder
from simulation.ai.api import Tactic, Aggressiveness, Personality
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext
from simulation.decisions.portfolio_manager import PortfolioManager

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
        
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, market_data, goods_list
        )
        
        # --- [Phase 4.5] Organic Monetary Transmission: Utility Competition Model ---
        # Instead of a hard-coded command, we compare the "Value" of Current Consumption vs Future Savings.
        
        loan_market_data = market_data.get("loan_market", {})
        nominal_rate = loan_market_data.get("interest_rate", 0.05)
        
        # 1. Savings Utility (Saving ROI)
        savings_roi = self._calculate_savings_roi(household, nominal_rate)
        # Apply 3-Pillars Preference (Wealth Pillar)
        savings_roi *= household.preference_asset
        
        # 2. Debt Burden (Income Effect) - Still a hard constraint for liquidity
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
            # If household already has a functioning durable asset of this type,
            # marginal utility is near zero.
            if hasattr(household, 'durable_assets'):
                 existing_durables = [a for a in household.durable_assets if a['item_id'] == item_id]
                 # Saturation Check: Own it OR have it in inventory (pending install)
                 has_inventory = household.inventory.get(item_id, 0.0) >= 1.0

                 if existing_durables or has_inventory:
                     # Already own it. Don't buy another unless replacing?
                     # Spec says: "If Household already has functioning asset, Marginal Utility drops near zero."
                     # Implementation: Skip purchase logic or force agg_buy to 0.
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
            # Apply preference weights based on good type (Luxury -> Social, Basic -> Growth)
            preference_weight = household.preference_social if is_luxury else household.preference_growth
            consumption_roi = (max_need_value / (avg_price + 1e-9)) * preference_weight
            
            # If Saving is more attractive, attenuate aggressiveness
            if savings_roi > consumption_roi:
                # Organic attenuation: ratio of ROIs
                attenuation = consumption_roi / (savings_roi + 1e-9)
                # Cap attenuation to prevent complete freeze unless extremely high rate
                # Ensure survival priority
                if max_need_value > 40:
                    attenuation = max(0.5, attenuation)
                else:
                    attenuation = max(0.1, attenuation)
                agg_buy *= attenuation
            
            if random.random() < 0.05: # Log 5% of decisions
                self.logger.info(
                    f"MONETARY_TRANS | HH {household.id} | {item_id} | Need: {max_need_value:.1f} | "
                    f"ConsROI: {consumption_roi:.2f} vs SavROI: {savings_roi:.4f} | AggBuy: {agg_buy:.2f}"
                )
            
            agg_buy *= debt_penalty # Apply liquidity constraint
            agg_buy = max(0.0, agg_buy)

            if random.random() < 0.001:
                self.logger.debug(
                    f"MONETARY_TRANS | Agent {household.id} {item_id}: "
                    f"SavROI: {savings_roi:.4f} vs ConsROI: {consumption_roi:.4f} -> Agg: {agg_buy:.2f}"
                )
            
            good_info = self.config_module.GOODS.get(item_id, {})
            utility_effects = good_info.get("utility_effects", {})
            
            # Improved Valuation: Anchor to Market Price + Urgent Need
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_current_sell_price", self.config_module.MARKET_PRICE_FALLBACK)
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

            # --- Phase 17-4: Veblen Demand Effect ---
            if getattr(self.config_module, "ENABLE_VANITY_SYSTEM", False) and good_info.get("is_veblen", False):
                # Price ↑ → Demand/WTP ↑
                # Prestige Value = Price * 0.1 * Conformity
                # Boost WTP to reflect this perceived utility
                conformity = getattr(household, "conformity", 0.5)
                prestige_boost = avg_price * 0.1 * conformity
                willingness_to_pay += prestige_boost

                # Also boost aggressiveness slightly to ensure purchase consideration
                agg_buy = min(1.0, agg_buy * (1.0 + 0.2 * conformity))
            
            # 3. Execution: Multi-unit Purchase Logic (Bulk Buying)
            # If need is high (> 70) or agg_buy is very high, buy more units.
            max_q = self.config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY
            
            target_quantity = 1.0
            
            if max_need_value > self.config_module.BULK_BUY_NEED_THRESHOLD:
                target_quantity = max_q
            elif agg_buy > self.config_module.BULK_BUY_AGG_THRESHOLD:
                target_quantity = max(1.0, max_q * self.config_module.BULK_BUY_MODERATE_RATIO) # Moderate panic
            
            # --- Phase 8: Inflation Psychology (Hoarding & Delay) ---
            # Apply Hoarding or Delay based on Expected Inflation
            expected_inflation = household.expected_inflation.get(item_id, 0.0)
            
            if expected_inflation > getattr(self.config_module, "PANIC_BUYING_THRESHOLD", 0.05):
                # Panic Buying: Increase Quantity and Willingness to Pay
                hoarding_factor = getattr(self.config_module, "HOARDING_FACTOR", 0.5)
                target_quantity *= (1.0 + hoarding_factor)
                willingness_to_pay *= (1.0 + expected_inflation) # Paying premium to secure goods
                
            elif expected_inflation < getattr(self.config_module, "DEFLATION_WAIT_THRESHOLD", -0.05):
                # Deflationary Wait: Decrease Quantity
                delay_factor = getattr(self.config_module, "DELAY_FACTOR", 0.5)
                target_quantity *= (1.0 - delay_factor)
                willingness_to_pay *= (1.0 + expected_inflation) # Lower WTP (expecting drop)
            
            # Budget Constraint Check: Don't spend more than 50% of assets on a single item per tick
            # unless survival is critical.
            budget_limit = household.assets * self.config_module.BUDGET_LIMIT_NORMAL_RATIO
            if max_need_value > self.config_module.BUDGET_LIMIT_URGENT_NEED:
                budget_limit = household.assets * self.config_module.BUDGET_LIMIT_URGENT_RATIO # Extreme urgency
            
            if willingness_to_pay * target_quantity > budget_limit:
                # Reduce quantity first
                target_quantity = budget_limit / willingness_to_pay
            
            # Final Sanity Check
            if target_quantity >= self.config_module.MIN_PURCHASE_QUANTITY and willingness_to_pay > 0:
                # Use int for durables, float for others
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
             
        # Scenario A: Already Employed - Monitor market for better wages
        if household.is_employed:
            # --- Phase 21.6: Wage Recovery (Adaptive) ---
            recovery_rate = getattr(self.config_module, "WAGE_RECOVERY_RATE", 0.01)
            household.wage_modifier *= (1.0 + recovery_rate)
            household.wage_modifier = min(1.0, household.wage_modifier)
            # --------------------------------------------

            # Mobility Lever: AI determines how much of a gap triggers a quit
            agg_mobility = action_vector.job_mobility_aggressiveness
            
            # Threshold: 1.0 (if agg=1.0) to 2.0 (if agg=0.0)
            quit_threshold = self.config_module.JOB_QUIT_THRESHOLD_BASE - agg_mobility
            
            # 1. Quitting if market metrics exceed the threshold
            if (market_avg_wage > household.current_wage * quit_threshold or 
                best_market_offer > household.current_wage * quit_threshold):
                
                # Probability scales with mobility intent
                if random.random() < (self.config_module.JOB_QUIT_PROB_BASE + agg_mobility * self.config_module.JOB_QUIT_PROB_SCALE):
                    household.quit()

        # Scenario B: Unemployed (Default or just quit) - Always look for work
        if not household.is_employed:
            # --- Phase 21.6: Adaptive Wage Logic & Survival Override ---

            # 1. Update Wage Modifier (Adaptive)
            decay_rate = getattr(self.config_module, "WAGE_DECAY_RATE", 0.02)
            floor_mod = getattr(self.config_module, "RESERVATION_WAGE_FLOOR", 0.3)
            household.wage_modifier *= (1.0 - decay_rate)
            household.wage_modifier = max(floor_mod, household.wage_modifier)

            # 2. Survival Trigger (Panic Mode)
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
                # Normal Adaptive Wage
                labor_market_info = market_data.get("goods_market", {}).get("labor", {})
                market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
                reservation_wage = market_avg_wage * household.wage_modifier

            # 3. Generate Order
            # Retrieve Market Data
            labor_market_info = market_data.get("goods_market", {}).get("labor", {})
            market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
            best_market_offer = labor_market_info.get("best_wage_offer", 0.0)

            # Refuse labor supply if market offer is too low (only if NOT panic)
            effective_offer = best_market_offer if best_market_offer > 0 else market_avg_wage
            # [Fix] Use dynamic reservation_wage as floor, not fixed 0.7 ratio
            # wage_floor = market_avg_wage * getattr(self.config_module, "RESERVATION_WAGE_FLOOR_RATIO", 0.7)
            wage_floor = reservation_wage

            if not is_panic and effective_offer < wage_floor:
                self.logger.info(
                    f"RESERVATION_WAGE | Household {household.id} refused labor. "
                    f"Offer: {effective_offer:.2f} < Floor: {wage_floor:.2f} (Avg: {market_avg_wage:.2f}, Mod: {household.wage_modifier:.2f})",
                    extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_refusal"]}
                )
                # Skip order generation
            else:
                orders.append(
                    Order(household.id, "SELL", "labor", 1, reservation_wage, "labor")
                )

        # ---------------------------------------------------------
        # 4. Execution: Stock Investment Logic
        # ---------------------------------------------------------
        stock_orders = self._make_stock_investment_decisions(
            household, markets, market_data, action_vector, current_time
        )
        # Current: Submit stock orders directly to markets
        stock_market = markets.get("stock_market")
        if stock_market is not None:
            for stock_order in stock_orders:
                stock_market.place_order(stock_order, current_time)

        # ---------------------------------------------------------
        # 5. Liquidity Management (Banking & Portfolio)
        # ---------------------------------------------------------
        # Phase 16: Portfolio Manager (WO-026)
        # Run monthly rebalancing (every 30 ticks)
        if current_time % 30 == 0:
            portfolio_orders = self._manage_portfolio(household, market_data, current_time)
            orders.extend(portfolio_orders)
        else:
            # Simple liquidity check for emergencies (Withdraw if cash is critical)
            emergency_orders = self._check_emergency_liquidity(household, market_data, current_time)
            orders.extend(emergency_orders)

        # ---------------------------------------------------------
        # 6. Real Estate Logic (Phase 17-3B)
        # ---------------------------------------------------------
        # Phase 17-4: Mimicry & Housing Logic
        if "housing" in markets:
             housing_market = markets["housing"]

             # Initialize Housing Manager
             from simulation.decisions.housing_manager import HousingManager
             housing_manager = HousingManager(household, self.config_module)

             # 1. Check Mimicry Trigger (High Priority)
             # Needs Reference Standard from market_data
             reference_standard = market_data.get("reference_standard", {})
             mimicry_intent = housing_manager.decide_mimicry_purchase(reference_standard)

             is_owner_occupier = household.residing_property_id in household.owned_properties
             should_search = (not is_owner_occupier) or (mimicry_intent is not None)

             if should_search:
                 # Look at best sell order (cheapest for now)
                 best_offer = None
                 min_price = float('inf')
                 
                 # housing_market.sell_orders is Dict[item_id, List[Order]]
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

                     # A. Mimicry Override
                     if mimicry_intent:
                         should_buy = True # Force buy
                         # Could adjust willingness to pay?
                         # Panic buy -> Pay whatever ask?
                         # For now, we match Ask Price.

                     # B. Rational Economic Logic
                     elif not is_owner_occupier:
                         should_buy = housing_manager.should_buy(
                             best_offer.price,
                             self.config_module.INITIAL_RENT_PRICE,
                             mortgage_rate
                         )

                     if should_buy:
                         # Place BUY Order
                         buy_order = Order(
                             household.id, "BUY", best_offer.item_id, 1.0, best_offer.price, "real_estate"
                         )
                         orders.append(buy_order)

                         if mimicry_intent:
                             self.logger.info(
                                 f"MIMICRY_BUY | Household {household.id} panic buying housing due to relative deprivation.",
                                 extra={"tick": current_time, "agent_id": household.id}
                             )

        return orders, action_vector

    def _manage_portfolio(self, household: "Household", market_data: Dict[str, Any], current_time: int) -> List[Order]:
        """
        Executes Portfolio Optimization (WO-026).
        """
        orders = []

        # 1. Gather Inputs
        # a. Liquid Assets
        cash = household.assets
        deposit_data = market_data.get("deposit_data", {})
        deposit_balance = deposit_data.get(household.id, 0.0)
        total_liquid = cash + deposit_balance

        # b. Risk Parameters
        risk_aversion = getattr(household, "risk_aversion", 1.0)

        # c. Market Rates
        loan_market = market_data.get("loan_market", {})
        risk_free_rate = loan_market.get("interest_rate", 0.05) # Base Rate

        # d. Equity Return Proxy
        # Assuming Equity Return ~ Dividend Yield + Growth?
        # Or simple constant for now (Startup ROI expectation).
        # Let's use a config value or assumed market average.
        # Startups usually target high ROI (e.g. 15-20%).
        equity_return = getattr(self.config_module, "EXPECTED_STARTUP_ROI", 0.15)

        # e. Survival Cost (Monthly)
        # Basic Food Price * Consumption * 30
        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        daily_consumption = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        monthly_survival_cost = food_price * daily_consumption * 30.0

        # f. Inflation Expectation (Avg of all goods)
        if household.expected_inflation:
            avg_inflation = sum(household.expected_inflation.values()) / len(household.expected_inflation)
        else:
            avg_inflation = 0.0

        # 2. Optimize
        target_cash, target_deposit, target_equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=total_liquid,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
            equity_return_proxy=equity_return,
            survival_cost=monthly_survival_cost,
            inflation_expectation=avg_inflation
        )

        # 3. Generate Orders

        # A. Deposit / Withdraw
        # Compare Target Deposit vs Current Deposit
        diff_deposit = target_deposit - deposit_balance

        if diff_deposit > 10.0:
            # Need to Deposit
            # Ensure we have enough cash (we should, based on optimization logic)
            actual_deposit = min(cash, diff_deposit)
            if actual_deposit > 10.0:
                orders.append(Order(household.id, "DEPOSIT", "currency", actual_deposit, 1.0, "currency"))

        elif diff_deposit < -10.0:
            # Need to Withdraw
            amount_to_withdraw = abs(diff_deposit)
            orders.append(Order(household.id, "WITHDRAW", "currency", amount_to_withdraw, 1.0, "currency"))

        # B. Investment (Startup)
        # If target_equity > 0, we want to invest.
        # Since currently "Equity" means "Startup" (until stock market participation is fuller),
        # we check if we can afford a startup.
        # Note: Startup Cost is high (~30,000). Optimization might suggest allocating 5,000.
        # In that case, we can't startup yet. We just keep it in deposit (accumulator).
        # OR we treat "Equity" allocation as "Willingness to spend on Capital".

        startup_cost = getattr(self.config_module, "STARTUP_COST", 30000.0)

        # If we have enough liquid assets allocated to Equity (or implicitly available) to start a firm
        # AND we don't own too many firms?
        # The Portfolio Manager says "Allocate X to Equity".
        # If X >= Startup Cost, we trigger INVEST.

        if target_equity >= startup_cost * 0.8: # Threshold to trigger
            # Generate INVEST order
            # Engine will handle the actual deduction and check
            # We only generate if we actually have the cash/deposit.
            # Usually Startup requires CASH.
            # If we just Deposited everything, we might fail.
            # But the Engine runs orders sequentially. DEPOSIT might happen first.
            # So we should be careful.
            # If we plan to INVEST, we should NOT DEPOSIT that amount.
            # Correction: optimize_portfolio returned target states.
            # If target_equity is high, target_deposit would be lower.
            # So we should hold that amount in CASH?
            # optimize_portfolio assumes Equity is an asset class.
            # If we can't buy Equity immediately (e.g. startup cost too high),
            # we should probably hold it in Interest-bearing Deposit until we have enough.
            # BUT, the WO says "Generate INVEST orders... if surplus exists".

            # Let's check if we *already* have enough CASH to invest?
            # Or if we *will* have enough after rebalancing?
            # If target_equity implies we should have equity, and we don't, we try to acquire.

            # Current Simplification:
            # If calculated target_equity is substantial, we try to INVEST.
            # We assume the agent keeps the money in Cash if they intend to Invest this turn,
            # OR withdraws it.
            # Since INVEST is processed by Engine, which checks Assets.
            # If we just sent a DEPOSIT order, Assets will decrease.
            # Thus, if we order INVEST, we should cancel the DEPOSIT of that amount.

            # Let's refine:
            # If we decide to INVEST, we treat that amount as "Spending" logic, not Deposit.
            # So we shouldn't have deposited it.
            # But diff_deposit was calculated based on target_deposit.
            # Target Deposit didn't include Target Equity.
            # So Cash should hold Target Equity + Target Cash.
            # If Cash > Target Cash + Target Equity, we Deposit surplus.
            pass # Logic is sound. target_deposit does NOT include equity funds.
                 # So equity funds remain in Cash (Wallet).

            # Now, simply check if we have enough Cash (after planned deposit/withdraw)
            # SURVIVAL BUFFER (Phase 23.5 Fix)
            # Households must keep a buffer for food/tax before investing everything.
            projected_cash = cash - max(0, diff_deposit) + max(0, -diff_deposit)
            survival_buffer = 2000.0

            if projected_cash >= (startup_cost + survival_buffer):
                orders.append(Order(household.id, "INVEST", "startup", 1.0, startup_cost, "admin"))

        return orders

    def _check_emergency_liquidity(self, household: "Household", market_data: Dict[str, Any], current_time: int) -> List[Order]:
        """
        Simple check between rebalancing periods to prevent starvation if Cash reaches 0.
        """
        orders = []
        if household.assets < 10.0:
            deposit_data = market_data.get("deposit_data", {})
            deposit_balance = deposit_data.get(household.id, 0.0)

            if deposit_balance > 10.0:
                # Emergency Withdraw
                amount = min(deposit_balance, 50.0) # Withdraw a small buffer
                orders.append(Order(household.id, "WITHDRAW", "currency", amount, 1.0, "currency"))

        return orders

    def _make_stock_investment_decisions(
        self,
        household: "Household",
        markets: Dict[str, Any],
        market_data: Dict[str, Any],
        action_vector: Any,
        current_time: int,
    ) -> List[StockOrder]:
        """주식 투자 의사결정을 수행합니다."""
        stock_orders: List[StockOrder] = []
        
        # 주식 시장 활성화 확인
        if not getattr(self.config_module, "STOCK_MARKET_ENABLED", False):
            return stock_orders
        
        stock_market = markets.get("stock_market")
        if stock_market is None:
            return stock_orders

        if household.assets < self.config_module.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT:
            return stock_orders  # Survival first

        # Get market metrics
        avg_dividend_yield = market_data.get("avg_dividend_yield", 0.05)
        risk_free_rate = market_data.get("loan_market", {}).get("interest_rate", 0.03)

        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        if not food_price or food_price <= 0:
            food_price = self.config_module.GOODS.get("basic_food", {}).get("initial_price", 5.0)
        daily_consumption = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        survival_cost = food_price * daily_consumption * 30.0

        # Risk aversion based on personality
        risk_aversion = self._get_risk_aversion(household.personality)

        # Optimize allocation
        target_cash, target_deposit, target_equity = PortfolioManager.optimize_portfolio(
            total_liquid_assets=household.assets,
            risk_aversion=risk_aversion,
            risk_free_rate=risk_free_rate,
            equity_return_proxy=avg_dividend_yield,
            survival_cost=survival_cost,
            inflation_expectation=market_data.get("inflation", 0.02)
        )

        # Calculate delta and place orders
        current_prices = {firm_id: stock_market.get_stock_price(firm_id) for firm_id in household.portfolio.holdings.keys()}
        current_equity_value = household.portfolio.get_valuation(current_prices)
        equity_delta = target_equity - current_equity_value

        if equity_delta > self.config_module.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD:  # Buy threshold
            stock_orders.extend(self._place_buy_orders(household, equity_delta, stock_market, current_time))
        elif equity_delta < -self.config_module.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD:  # Sell threshold
            stock_orders.extend(self._place_sell_orders(household, -equity_delta, stock_market, current_time))
        
        return stock_orders

    def _get_risk_aversion(self, personality_type: Personality) -> float:
        if personality_type == Personality.STATUS_SEEKER:
            return 0.5
        elif personality_type == Personality.CONSERVATIVE:
            return 5.0
        return 2.0

    def _place_buy_orders(self, household: "Household", amount_to_invest: float, stock_market: Any, tick: int) -> List[StockOrder]:
        orders = []
        # Simplified: Invest in a few random stocks
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

    def _place_sell_orders(self, household: "Household", amount_to_sell: float, stock_market: Any, tick: int) -> List[StockOrder]:
        orders = []
        # Simplified: Sell from largest holdings first
        sorted_holdings = sorted(
            household.portfolio.holdings.items(),
            key=lambda item: item[1] * stock_market.get_stock_price(item[0]),
            reverse=True
        )

        for firm_id, quantity in sorted_holdings:
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

    def _calculate_savings_roi(self, household: "Household", nominal_rate: float) -> float:
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
        household = context.household
        if not household: return False

        agent_data = household.get_agent_data()
        market_data = context.market_data

        return self.ai_engine.decide_reproduction(agent_data, market_data, context.current_time)
