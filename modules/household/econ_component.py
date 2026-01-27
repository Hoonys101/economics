from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from collections import deque, defaultdict
import math
import random
import logging

from modules.household.api import IEconComponent
from modules.household.dtos import EconStateDTO, EconContextDTO
from simulation.dtos import ConsumptionResult, LaborResult, StressScenarioConfig
from simulation.models import Order, Skill
from simulation.utils.shadow_logger import log_shadow
from simulation.ai.household_system2 import HousingDecisionInputs

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

class EconComponent(IEconComponent):
    """
    Stateless component managing economic aspects of the Household.
    Operates on EconStateDTO.
    """

    def update_wage_dynamics(self, state: EconStateDTO, config: Any, is_employed: bool) -> EconStateDTO:
        new_state = state.copy()

        if is_employed:
            recovery_rate = getattr(config, "WAGE_RECOVERY_RATE", 0.01)
            new_state.wage_modifier = min(1.0, new_state.wage_modifier * (1.0 + recovery_rate))
        else:
            decay_rate = getattr(config, "WAGE_DECAY_RATE", 0.02)
            floor_mod = getattr(config, "RESERVATION_WAGE_FLOOR", 0.3)
            new_state.wage_modifier = max(floor_mod, new_state.wage_modifier * (1.0 - decay_rate))

        return new_state

    def consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        item_id: str,
        quantity: float,
        current_time: int,
        goods_info: Dict[str, Any],
        config: Any
    ) -> Tuple[EconStateDTO, Dict[str, float], ConsumptionResult]:
        """
        Consumes an item, updating inventory, consumption tracking, and needs.
        Logic migrated from EconomyManager.consume.
        """
        new_state = state.copy()
        new_needs = needs.copy()

        is_service = goods_info.get("is_service", False)
        inventory_qty = new_state.inventory.get(item_id, 0.0)

        if is_service or inventory_qty >= quantity:
            if not is_service:
                new_state.inventory[item_id] = max(0.0, inventory_qty - quantity)

            # Durable goods logic
            is_durable = goods_info.get("is_durable", False)
            if is_durable and not is_service:
                base_lifespan = goods_info.get("base_lifespan", 50)
                quality = new_state.inventory_quality.get(item_id, 1.0)
                num_assets = int(round(quantity))
                for _ in range(num_assets):
                    asset = {
                        "item_id": item_id,
                        "quality": quality,
                        "remaining_life": base_lifespan,
                    }
                    new_state.durable_assets.append(asset)

            # Education XP logic
            if item_id == "education_service":
                learning_efficiency = getattr(config, "LEARNING_EFFICIENCY", 0.1)
                xp_gain = quantity * learning_efficiency
                new_state.education_xp += xp_gain

            # Consumption Value
            fallback_price = getattr(config, "DEFAULT_FALLBACK_PRICE", 5.0)
            price = new_state.perceived_avg_prices.get(item_id, fallback_price)
            consumption_value = quantity * price

            new_state.current_consumption += consumption_value

            # Food tracking
            if item_id in ["food", "basic_food", "luxury_food"]:
                new_state.current_food_consumption += consumption_value

            # Utility / Needs
            total_utility = 0.0
            utility_map = goods_info.get("utility_effects") or goods_info.get("utility_per_need")
            if utility_map:
                for need_type, utility_value in utility_map.items():
                    if need_type in new_needs:
                        satisfaction_gain = utility_value * quantity
                        total_utility += satisfaction_gain
                        new_needs[need_type] = max(0.0, new_needs.get(need_type, 0.0) - satisfaction_gain)

            return new_state, new_needs, ConsumptionResult(items_consumed={item_id: quantity}, satisfaction=total_utility)

        return new_state, new_needs, ConsumptionResult(items_consumed={}, satisfaction=0.0)

    def decide_and_consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        current_time: int,
        goods_info_map: Dict[str, Any],
        config: Any
    ) -> Tuple[EconStateDTO, Dict[str, float], Dict[str, float]]:
        """
        Decides what to consume from inventory based on needs and executes consumption.
        Logic ported from ConsumptionBehavior.
        """
        new_state = state # We will update state iteratively via consume, which returns new state
        # But wait, consume returns new state every time.
        # If we loop, we must chain updates.

        final_needs = needs.copy()
        consumed_items: Dict[str, float] = {}

        # Iterate over inventory items
        # We need to copy inventory keys to iterate safely while potentially modifying
        inventory_items = list(state.inventory.items())

        for item_id, inventory_quantity in inventory_items:
            if inventory_quantity <= 0:
                continue

            good_info = goods_info_map.get(item_id)
            if not good_info:
                continue

            utility_effects = good_info.get("utility_effects", {})
            if not utility_effects:
                continue

            should_consume = False
            for need_key, effect in utility_effects.items():
                current_need = final_needs.get(need_key, 0.0)

                # Consumption Threshold
                threshold = getattr(config, "NEED_MEDIUM_THRESHOLD", 50.0)
                if need_key == "survival":
                    threshold = getattr(config, "SURVIVAL_NEED_CONSUMPTION_THRESHOLD", 20.0)

                if current_need > threshold:
                    should_consume = True
                    break

            if should_consume:
                is_durable = good_info.get("is_durable", False)
                if is_durable:
                    if inventory_quantity < 1.0:
                        continue
                    quantity_to_consume = 1.0
                else:
                    quantity_to_consume = min(inventory_quantity, 1.0)

                if quantity_to_consume > 0:
                    # Call consume logic
                    # We call self.consume but we must pass the *current* updated state
                    new_state, updated_needs, _ = self.consume(
                        new_state,
                        final_needs,
                        item_id,
                        quantity_to_consume,
                        current_time,
                        good_info,
                        config
                    )
                    final_needs = updated_needs
                    consumed_items[item_id] = consumed_items.get(item_id, 0.0) + quantity_to_consume

        return new_state, final_needs, consumed_items

    def work(self, state: EconStateDTO, hours: float, config: Any) -> Tuple[EconStateDTO, LaborResult]:
        """
        Executes work logic (non-financial).
        Logic migrated from LaborManager.work.
        """
        new_state = state.copy()

        if not new_state.is_employed or new_state.employer_id is None:
            return new_state, LaborResult(hours_worked=0, income_earned=0)

        income = new_state.current_wage * hours
        # Note: We do NOT add assets here. TransactionProcessor handles wages.

        return new_state, LaborResult(hours_worked=hours, income_earned=income)

    def update_skills(self, state: EconStateDTO, config: Any) -> EconStateDTO:
        """
        Updates labor skills based on experience.
        Logic migrated from LaborManager.update_skills.
        """
        new_state = state.copy()

        log_growth = math.log1p(new_state.education_xp) # ln(x+1)
        talent_factor = new_state.talent.base_learning_rate
        new_skill_val = 1.0 + (log_growth * talent_factor)

        new_state.labor_skill = new_skill_val

        return new_state

    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: EconContextDTO,
        orders: List[Order],
        stress_scenario_config: Optional[StressScenarioConfig] = None,
        config: Any = None
    ) -> Tuple[EconStateDTO, List[Order]]:
        """
        Refines orders and updates internal economic state.
        Includes System 2 Housing Logic and Shadow Wage Logic.
        """
        new_state = state.copy()
        refined_orders = list(orders) # Copy list

        market_data = context.market_data
        current_time = context.current_time
        markets = context.markets

        # 1. System 2 Housing Decision Logic (Ported from HouseholdSystem2Planner)
        if new_state.is_homeless or current_time % 30 == 0:
            housing_market = market_data.get("housing_market", {})
            loan_market = market_data.get("loan_market", {})

            market_rent = housing_market.get("avg_rent_price", 100.0)
            market_price = housing_market.get("avg_sale_price")
            if not market_price:
                 market_price = market_rent * 12 * 20.0

            new_state.housing_price_history.append(market_price)
            risk_free_rate = loan_market.get("interest_rate", 0.05)

            price_growth = 0.0
            if len(new_state.housing_price_history) >= 2:
                start_price = new_state.housing_price_history[0]
                end_price = new_state.housing_price_history[-1]
                if start_price > 0:
                    price_growth = (end_price - start_price) / start_price

            ticks_per_year = getattr(config, "TICKS_PER_YEAR", 100)

            income = new_state.current_wage * ticks_per_year if new_state.is_employed else new_state.expected_wage * ticks_per_year

            inputs = HousingDecisionInputs(
                current_wealth=new_state.assets,
                annual_income=income,
                market_rent_monthly=market_rent,
                market_price=market_price,
                risk_free_rate=risk_free_rate,
                price_growth_expectation=price_growth
            )

            # Decide BUY vs RENT
            # Logic: Calculate NPV
            # Ported logic from HouseholdSystem2Planner.decide

            # 1. Safety Guardrail (DTI)
            loan_amount = inputs.market_price * 0.8
            annual_mortgage_cost = loan_amount * inputs.risk_free_rate
            dti_threshold = inputs.annual_income * 0.4

            decision = "RENT" # Default
            if annual_mortgage_cost <= dti_threshold:
                 # 2. Rational Choice (Simplified NPV logic or full calculation)
                 # Full calculation logic:
                 T_years = 10
                 T_months = T_years * 12
                 r_monthly = (inputs.risk_free_rate + 0.02) / 12.0

                 P_initial = inputs.market_price
                 U_shelter = inputs.market_rent_monthly
                 Cost_own = (P_initial * 0.01) / 12.0

                 cap = getattr(config, "HOUSING_EXPECTATION_CAP", 0.05)
                 g_annual = min(inputs.price_growth_expectation, cap)
                 P_future = P_initial * ((1.0 + g_annual) ** T_years)

                 Principal = P_initial * 0.2
                 Income_invest = Principal * (inputs.risk_free_rate / 12.0)
                 Cost_rent = inputs.market_rent_monthly

                 npv_buy_flow = 0.0
                 npv_rent_flow = 0.0

                 for t in range(1, T_months + 1):
                     discount_factor = (1.0 + r_monthly) ** t
                     npv_buy_flow += (U_shelter - Cost_own) / discount_factor
                     npv_rent_flow += (Income_invest - Cost_rent) / discount_factor

                 terminal_discount = (1.0 + r_monthly) ** T_months
                 term_val_buy = P_future / terminal_discount
                 npv_buy = npv_buy_flow + term_val_buy - P_initial

                 term_val_rent = Principal / terminal_discount
                 npv_rent = npv_rent_flow + term_val_rent

                 if npv_buy > npv_rent:
                     decision = "BUY"

            new_state.housing_target_mode = decision

        # 2. Shadow Labor Market Logic
        avg_market_wage = 0.0
        if market_data and "labor" in market_data:
             avg_market_wage = market_data["labor"].get("avg_wage", 0.0)

        if avg_market_wage > 0:
            new_state.market_wage_history.append(avg_market_wage)

        if new_state.shadow_reservation_wage <= 0.0:
            new_state.shadow_reservation_wage = new_state.current_wage if new_state.is_employed else new_state.expected_wage

        if new_state.is_employed:
            target = max(new_state.current_wage, new_state.shadow_reservation_wage)
            new_state.shadow_reservation_wage = (new_state.shadow_reservation_wage * 0.95) + (target * 0.05)
        else:
            new_state.shadow_reservation_wage *= (1.0 - 0.02)
            min_wage = getattr(config, "HOUSEHOLD_MIN_WAGE_DEMAND", 6.0)
            if new_state.shadow_reservation_wage < min_wage:
                new_state.shadow_reservation_wage = min_wage

        # 3. Generate Housing Orders
        if new_state.housing_target_mode == "BUY" and new_state.is_homeless:
            housing_market_obj = markets.get("housing")
            if housing_market_obj:
                target_unit_id = None
                best_price = float('inf')

                # Check for available units (Assuming generic access to sell_orders)
                if hasattr(housing_market_obj, "sell_orders"):
                    for item_id, sell_orders in housing_market_obj.sell_orders.items():
                        if item_id.startswith("unit_") and sell_orders:
                            ask_price = sell_orders[0].price
                            if ask_price < best_price:
                                best_price = ask_price
                                target_unit_id = item_id

                if target_unit_id:
                     down_payment = best_price * 0.2
                     if new_state.assets >= down_payment:
                         buy_order = Order(
                             agent_id=state.portfolio.owner_id, # Using owner_id from portfolio as proxy for ID
                             item_id=target_unit_id,
                             price=best_price,
                             quantity=1.0,
                             market_id="housing",
                             order_type="BUY"
                         )
                         refined_orders.append(buy_order)

        # 4. Panic Selling
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'deflation':
             threshold = getattr(config, "PANIC_SELLING_ASSET_THRESHOLD", 500.0)
             if new_state.assets < threshold:
                 # Sell stocks
                 for firm_id, share in new_state.portfolio.holdings.items():
                     if share.quantity > 0:
                         stock_order = Order(
                             agent_id=state.portfolio.owner_id,
                             order_type="SELL",
                             item_id=f"stock_{firm_id}",
                             quantity=share.quantity,
                             price=0.0,
                             market_id="stock_market"
                         )
                         refined_orders.append(stock_order)

        # 5. Targeted Order Refinement (Logic from original)
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'phase29_depression':
             multiplier = stress_scenario_config.demand_shock_multiplier
             if multiplier is not None:
                 for order in refined_orders:
                     if order.order_type == "BUY" and order.item_id not in ["labor", "loan"]:
                         if not order.item_id.startswith("stock_"):
                            order.quantity *= multiplier

        # 6. Forensics (Shadow Wage Update)
        for order in refined_orders:
             if order.order_type == "SELL" and (order.item_id == "labor" or order.market_id == "labor"):
                new_state.last_labor_offer_tick = current_time

        return new_state, refined_orders

    def update_perceived_prices(
        self,
        state: EconStateDTO,
        market_data: Dict[str, Any],
        goods_info_map: Dict[str, Any],
        stress_scenario_config: Optional[StressScenarioConfig],
        config: Any
    ) -> EconStateDTO:
        """
        Updates inflation expectations and price memory.
        """
        new_state = state.copy()
        goods_market = market_data.get("goods_market")
        if not goods_market:
            return new_state

        adaptive_rate = new_state.adaptation_rate
        if stress_scenario_config and stress_scenario_config.is_active:
            if stress_scenario_config.scenario_name == 'hyperinflation':
                if hasattr(stress_scenario_config, "inflation_expectation_multiplier"):
                     adaptive_rate *= stress_scenario_config.inflation_expectation_multiplier

        for item_id, good in goods_info_map.items():
            actual_price = goods_market.get(f"{item_id}_avg_traded_price")

            if actual_price is not None and actual_price > 0:
                history = new_state.price_history[item_id]
                if history:
                    last_price = history[-1]
                    if last_price > 0:
                        inflation_t = (actual_price - last_price) / last_price

                        old_expect = new_state.expected_inflation.get(item_id, 0.0)
                        new_expect = old_expect + adaptive_rate * (inflation_t - old_expect)
                        new_state.expected_inflation[item_id] = new_expect

                history.append(actual_price)

                old_perceived_price = new_state.perceived_avg_prices.get(
                    item_id, actual_price
                )
                update_factor = getattr(config, "PERCEIVED_PRICE_UPDATE_FACTOR", 0.1)
                new_perceived_price = (
                    update_factor * actual_price
                ) + (
                    (1 - update_factor)
                    * old_perceived_price
                )
                new_state.perceived_avg_prices[item_id] = new_perceived_price

        return new_state

    def prepare_clone_state(
        self,
        parent_state: EconStateDTO,
        parent_skills: Dict[str, Any],
        config: Any
    ) -> Dict[str, Any]:
        """
        Prepares initial economic state for a clone (inheritance logic).
        Returns a dictionary of kwargs for Household initialization or EconState values.
        """
        # Logic migrated from Household.apply_child_inheritance

        # Skill Inheritance
        new_skills = {}
        for domain, skill in parent_skills.items():
            # Assuming skill is object with domain, value, observability
            new_skills[domain] = Skill(
                domain=domain,
                value=skill.value * 0.2,
                observability=skill.observability
            )

        education_level = min(parent_state.education_level, 1)
        expected_wage = parent_state.expected_wage * 0.8

        return {
            "skills": new_skills,
            "education_level": education_level,
            "expected_wage": expected_wage,
            "labor_skill": parent_state.labor_skill,
            "aptitude": parent_state.aptitude
        }
