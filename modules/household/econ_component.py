from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from collections import deque
import logging
import math

from modules.household.api import IEconComponent
from modules.household.dtos import EconContextDTO, HouseholdStateDTO
from simulation.components.consumption_behavior import ConsumptionBehavior
from simulation.components.economy_manager import EconomyManager
from simulation.components.labor_manager import LaborManager
from simulation.components.market_component import MarketComponent
from simulation.portfolio import Portfolio
from simulation.ai.system2_planner import System2Planner
from simulation.ai.household_system2 import HouseholdSystem2Planner, HousingDecisionInputs
from simulation.models import Order, Skill
from simulation.utils.shadow_logger import log_shadow

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.dtos.scenario import StressScenarioConfig

class EconComponent(IEconComponent):
    """
    Manages economic state and behavior of the Household.
    Owns ConsumptionBehavior, LaborManager, EconomyManager, MarketComponent, Portfolio.
    """
    def __init__(self, owner: "Household", config_module: Any):
        self.owner = owner
        self.config_module = config_module
        self.logger = owner.logger

        # --- State ---
        self._assets: float = 0.0
        self._inventory: Dict[str, float] = {}

        # Labor State
        self.is_employed: bool = False
        self.employer_id: Optional[int] = None
        self.current_wage: float = 0.0
        self.wage_modifier: float = 1.0
        self.labor_skill: float = 1.0
        self.education_xp: float = 0.0
        self.education_level: int = 0
        self.expected_wage: float = 10.0
        self.last_labor_offer_tick: int = 0
        self.last_fired_tick: int = -1
        self.job_search_patience: int = 0

        # Real Estate State
        self.owned_properties: List[int] = []
        self.residing_property_id: Optional[int] = None
        self.is_homeless: bool = True
        self.housing_target_mode: str = "RENT"
        self.home_quality_score: float = 1.0

        # Misc State
        self.durable_assets: List[Dict[str, Any]] = []
        self.shares_owned: Dict[int, float] = {} # Keeping for legacy compat if needed

        # Income Tracking
        self.labor_income_this_tick: float = 0.0
        self.capital_income_this_tick: float = 0.0

        # --- Components ---
        self.consumption = ConsumptionBehavior(owner, config_module)
        self.economy_manager = EconomyManager(owner, config_module)
        self.labor_manager = LaborManager(owner, config_module)
        self.market_component = MarketComponent(owner, config_module)
        self.portfolio = Portfolio(owner.id)

        self.system2_planner = System2Planner(owner, config_module)
        self.housing_planner = HouseholdSystem2Planner(owner, config_module)

        # --- History ---
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", 100))
        self.housing_price_history: deque = deque(maxlen=ticks_per_year)
        self.market_wage_history: deque[float] = deque(maxlen=30)
        self.shadow_reservation_wage: float = 0.0

    @property
    def assets(self) -> float:
        return self._assets

    @assets.setter
    def assets(self, value: float) -> None:
        self._assets = value

    @property
    def inventory(self) -> Dict[str, float]:
        return self._inventory

    @property
    def home_quality_score(self) -> float:
        return self._home_quality_score

    @home_quality_score.setter
    def home_quality_score(self, value: float) -> None:
        self._home_quality_score = value

    @inventory.setter
    def inventory(self, value: Dict[str, float]) -> None:
        self._inventory = value

    def adjust_assets(self, delta: float) -> None:
        self._assets += delta

    def consume(self, item_id: str, quantity: float, current_time: int) -> Any:
        return self.economy_manager.consume(item_id, quantity, current_time)

    def get_state(self) -> HouseholdStateDTO:
        pass # Partially implemented if needed, but Household calls components

    def orchestrate_economic_decisions(self, context: EconContextDTO, orders: List[Order], stress_scenario_config: Optional["StressScenarioConfig"] = None) -> List[Order]:
        """
        Refines and adds to the orders based on System 2 logic, panic rules, and other economic constraints.
        """
        market_data = context.market_data
        current_time = context.current_time
        markets = context.markets

        # 1. System 2 Housing Decision (Run Logic)
        self._decide_housing(market_data, current_time)

        # 2. Shadow Labor Market Logic
        self._calculate_shadow_reservation_wage(market_data, current_time)

        # 3. Execute System 2 Housing Decision (Generate Orders)
        if self.housing_target_mode == "BUY" and self.is_homeless:
            housing_market = markets.get("housing")
            if housing_market:
                target_unit_id = None
                best_price = float('inf')

                # Check for available units
                if hasattr(housing_market, "sell_orders"):
                    for item_id, sell_orders in housing_market.sell_orders.items():
                        if item_id.startswith("unit_") and sell_orders:
                            ask_price = sell_orders[0].price
                            if ask_price < best_price:
                                best_price = ask_price
                                target_unit_id = item_id

                if target_unit_id:
                     # Check affordability (20% down payment)
                     down_payment = best_price * 0.2
                     if self.assets >= down_payment:
                         buy_order = Order(
                             agent_id=self.owner.id,
                             item_id=target_unit_id,
                             price=best_price,
                             quantity=1.0,
                             market_id="housing",
                             order_type="BUY"
                         )
                         orders.append(buy_order)
                         self.logger.info(f"HOUSING_BUY | Household {self.owner.id} decided to buy {target_unit_id} at {best_price}")

        # 4. Panic Selling (Deflation)
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'deflation':
             threshold = self.config_module.PANIC_SELLING_ASSET_THRESHOLD
             if self.assets < threshold:
                 self.logger.warning(f"PANIC_SELLING | Household {self.owner.id} panic selling stocks due to low assets ({self.assets:.1f})")
                 # Sell ALL stocks
                 for firm_id, share in self.portfolio.holdings.items():
                     if share.quantity > 0:
                         stock_order = Order(
                             agent_id=self.owner.id,
                             order_type="SELL",
                             item_id=f"stock_{firm_id}",
                             quantity=share.quantity,
                             price=0.0,
                             market_id="stock_market"
                         )
                         orders.append(stock_order)

        # 5. Targeted Order Refinement & Internal Commands (QUIT)
        refined_orders = []
        for order in orders:
            if order.order_type == "QUIT":
                self.owner.quit()
                continue # Do not forward QUIT order to markets

            if order.order_type == "BUY" and order.target_agent_id is None:
                # Select best seller
                best_seller_id, best_price = self.market_component.choose_best_seller(order.item_id, {"markets": markets})
                if best_seller_id:
                    order.target_agent_id = best_seller_id
            refined_orders.append(order)
        orders[:] = refined_orders

        # 6. Forensics
        for order in orders:
             if order.order_type == "SELL" and (order.item_id == "labor" or order.market_id == "labor"):
                self.last_labor_offer_tick = current_time

        return orders

    def _decide_housing(self, market_data: Dict[str, Any], current_time: int) -> None:
        """
        Executes System 2 Housing Logic.
        """
        if not (self.is_homeless or current_time % 30 == 0):
            return

        housing_market = market_data.get("housing_market", {})
        loan_market = market_data.get("loan_market", {})

        market_rent = housing_market.get("avg_rent_price", 100.0)
        market_price = housing_market.get("avg_sale_price")
        if not market_price:
             market_price = market_rent * 12 * 20.0

        self.housing_price_history.append(market_price)
        risk_free_rate = loan_market.get("interest_rate", 0.05)

        price_growth = 0.0
        if len(self.housing_price_history) >= 2:
            start_price = self.housing_price_history[0]
            end_price = self.housing_price_history[-1]
            if start_price > 0:
                price_growth = (end_price - start_price) / start_price

        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
        income = self.current_wage * ticks_per_year if self.is_employed else self.expected_wage * ticks_per_year

        inputs = HousingDecisionInputs(
            current_wealth=self.assets,
            annual_income=income,
            market_rent_monthly=market_rent,
            market_price=market_price,
            risk_free_rate=risk_free_rate,
            price_growth_expectation=price_growth
        )

        decision = self.housing_planner.decide(inputs)

        if decision != self.housing_target_mode:
            self.logger.info(
                f"HOUSING_DECISION_CHANGE | Household {self.owner.id} switched housing mode: {self.housing_target_mode} -> {decision}",
                extra={"tick": current_time, "agent_id": self.owner.id}
            )
            self.housing_target_mode = decision

    def _calculate_shadow_reservation_wage(self, market_data: Dict[str, Any], current_tick: int) -> None:
        """
        WO-056: Stage 1 Shadow Mode (Labor Market Mechanism).
        """
        avg_market_wage = 0.0
        if market_data and "labor" in market_data:
             avg_market_wage = market_data["labor"].get("avg_wage", 0.0)

        if avg_market_wage > 0:
            self.market_wage_history.append(avg_market_wage)

        startup_cost_index = 0.0
        if self.market_wage_history:
            avg_wage_30 = sum(self.market_wage_history) / len(self.market_wage_history)
            startup_cost_index = avg_wage_30 * 6.0

        if self.shadow_reservation_wage <= 0.0:
            self.shadow_reservation_wage = self.current_wage if self.is_employed else self.expected_wage

        if self.is_employed:
            target = max(self.current_wage, self.shadow_reservation_wage)
            self.shadow_reservation_wage = (self.shadow_reservation_wage * 0.95) + (target * 0.05)
        else:
            self.shadow_reservation_wage *= (1.0 - 0.02)
            min_wage = getattr(self.config_module, "HOUSEHOLD_MIN_WAGE_DEMAND", 6.0)
            if self.shadow_reservation_wage < min_wage:
                self.shadow_reservation_wage = min_wage

        log_shadow(
            tick=current_tick,
            agent_id=self.owner.id,
            agent_type="Household",
            metric="shadow_wage",
            current_value=self.current_wage if self.is_employed else self.expected_wage,
            shadow_value=self.shadow_reservation_wage,
            details=f"Employed={self.is_employed}, StartupIdx={startup_cost_index:.2f}"
        )
