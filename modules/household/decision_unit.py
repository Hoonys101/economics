from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import logging

from modules.household.api import IDecisionUnit, OrchestrationContextDTO
from modules.household.dtos import EconStateDTO
from simulation.dtos import StressScenarioConfig
from simulation.models import Order
from simulation.ai.household_system2 import HousingDecisionInputs

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import HouseholdConfigDTO

logger = logging.getLogger(__name__)

class DecisionUnit(IDecisionUnit):
    """
    Stateless unit responsible for coordinating decision making.
    Wraps DecisionEngine and System 2 logic (Orchestration).
    """

    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: OrchestrationContextDTO,
        initial_orders: List[Order]
    ) -> Tuple[EconStateDTO, List[Order]]:
        """
        Refines orders and updates internal economic state.
        Includes System 2 Housing Logic and Shadow Wage Logic.
        Logic migrated from EconComponent.orchestrate_economic_decisions.
        """
        new_state = state.copy()
        refined_orders = list(initial_orders) # Copy list

        # Unpack from DTO
        market_snapshot = context["market_snapshot"]
        current_time = context["current_time"]
        config = context["config"]
        stress_scenario_config = context["stress_scenario_config"]

        # 1. System 2 Housing Decision Logic (Ported from HouseholdSystem2Planner)
        if new_state.is_homeless or current_time % 30 == 0:
            housing_snapshot = market_snapshot.housing
            loan_snapshot = market_snapshot.loan

            market_rent = housing_snapshot.avg_rent_price
            market_price = housing_snapshot.avg_sale_price

            # Legacy fallback
            if market_price <= 0.001:
                 market_price = market_rent * 12 * 20.0

            new_state.housing_price_history.append(market_price)
            risk_free_rate = loan_snapshot.interest_rate

            price_growth = 0.0
            if len(new_state.housing_price_history) >= 2:
                start_price = new_state.housing_price_history[0]
                end_price = new_state.housing_price_history[-1]
                if start_price > 0:
                    price_growth = (end_price - start_price) / start_price

            ticks_per_year = config.ticks_per_year

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

                 cap = config.housing_expectation_cap
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
        avg_market_wage = market_snapshot.labor.avg_wage

        if avg_market_wage > 0:
            new_state.market_wage_history.append(avg_market_wage)

        if new_state.shadow_reservation_wage <= 0.0:
            new_state.shadow_reservation_wage = new_state.current_wage if new_state.is_employed else new_state.expected_wage

        if new_state.is_employed:
            target = max(new_state.current_wage, new_state.shadow_reservation_wage)
            new_state.shadow_reservation_wage = (new_state.shadow_reservation_wage * 0.95) + (target * 0.05)
        else:
            new_state.shadow_reservation_wage *= (1.0 - 0.02)
            min_wage = config.household_min_wage_demand
            if new_state.shadow_reservation_wage < min_wage:
                new_state.shadow_reservation_wage = min_wage

        # 3. Generate Housing Orders
        if new_state.housing_target_mode == "BUY" and new_state.is_homeless:
            target_unit = None
            best_price = float('inf')

            # Access market data ONLY from the snapshot DTO
            for unit_dto in market_snapshot.housing.for_sale_units:
                if unit_dto.price < best_price:
                    best_price = unit_dto.price
                    target_unit = unit_dto

            if target_unit:
                 down_payment = best_price * 0.2
                 if new_state.assets >= down_payment:
                     buy_order = Order(
                         agent_id=state.portfolio.owner_id,
                         side="BUY",
                         item_id=target_unit.unit_id,
                         quantity=1.0,
                         price_limit=best_price,
                         market_id="housing"
                     )
                     refined_orders.append(buy_order)

        # 4. Panic Selling
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'deflation':
             threshold = config.panic_selling_asset_threshold
             if new_state.assets < threshold:
                 # Sell stocks
                 for firm_id, share in new_state.portfolio.holdings.items():
                     if share.quantity > 0:
                         stock_order = Order(
                             agent_id=state.portfolio.owner_id,
                             side="SELL",
                             item_id=f"stock_{firm_id}",
                             quantity=share.quantity,
                             price_limit=0.0,
                             market_id="stock_market"
                         )
                         refined_orders.append(stock_order)

        # 5. Targeted Order Refinement (Logic from original)
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'phase29_depression':
             multiplier = stress_scenario_config.demand_shock_multiplier
             if multiplier is not None:
                 for order in refined_orders:
                     if order.side == "BUY" and hasattr(order, "item_id") and order.item_id not in ["labor", "loan"]:
                         if not order.item_id.startswith("stock_"):
                            order.quantity *= multiplier

        # 6. Forensics (Shadow Wage Update)
        for order in refined_orders:
             if order.side == "SELL" and (getattr(order, "item_id", "") == "labor" or order.market_id == "labor"):
                new_state.last_labor_offer_tick = current_time

        return new_state, refined_orders
