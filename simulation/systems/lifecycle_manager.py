# simulation/systems/lifecycle_manager.py

from __future__ import annotations
from typing import List, TYPE_CHECKING, Any
import logging

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.dtos.api import SimulationState

from simulation.systems.api import AgentLifecycleManagerInterface
from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.immigration_manager import ImmigrationManager
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.firm_management import FirmSystem
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner

class AgentLifecycleManager(AgentLifecycleManagerInterface):
    """에이전트의 생성, 노화, 사망, 청산을 처리합니다.
       WO-103: Implements SystemInterface.
    """

    def __init__(self, config_module: Any, demographic_manager: DemographicManager,
                 inheritance_manager: InheritanceManager, firm_system: FirmSystem, logger: logging.Logger):
        self.config = config_module
        self.demographic_manager = demographic_manager
        self.inheritance_manager = inheritance_manager
        self.firm_system = firm_system
        self.immigration_manager = ImmigrationManager(config_module=config_module)
        self.breeding_planner = VectorizedHouseholdPlanner(config_module)
        self.logger = logger

    def execute(self, state: SimulationState) -> None:
        """한 틱 동안 발생하는 모든 생명주기 관련 이벤트를 처리합니다."""

        # 1. Aging
        self.demographic_manager.process_aging(state.households, state.time)

        # 2. Births (출생)
        new_children = self._process_births(state)
        self._register_new_agents(state, new_children)

        # 3. Immigration (이민)
        # Duck typing: state serves as 'sim' for ImmigrationManager if it matches interface
        new_immigrants = self.immigration_manager.process_immigration(state)
        self._register_new_agents(state, new_immigrants)

        # 4. Entrepreneurship (창업) - FirmSystem과 협력
        self.firm_system.check_entrepreneurship(state)

        # 5. Death & Liquidation (사망 및 청산)
        self._handle_agent_liquidation(state)

    def _process_births(self, state: SimulationState) -> List[Household]:
        """(기존 `run_tick`의 출생 로직)"""
        birth_requests = []
        active_households = [h for h in state.households if h.is_active]
        if not active_households:
            return []

        decisions = self.breeding_planner.decide_breeding_batch(active_households)
        for h, decision in zip(active_households, decisions):
            if decision:
                birth_requests.append(h)

        return self.demographic_manager.process_births(state, birth_requests)

    def _register_new_agents(self, state: SimulationState, new_agents: List[Household]):
        """(기존 `run_tick`의 신규 에이전트 등록 로직)"""
        for agent in new_agents:
            state.households.append(agent)
            state.agents[agent.id] = agent
            agent.decision_engine.markets = state.markets
            agent.decision_engine.goods_data = state.goods_data

            if state.stock_market:
                for firm_id, qty in agent.shares_owned.items():
                    state.stock_market.update_shareholder(agent.id, firm_id, qty)

            # Add to AI training manager to ensure they are trained
            if state.ai_training_manager:
                state.ai_training_manager.agents.append(agent)

    def _calculate_inventory_value(self, inventory: dict, markets: dict) -> float:
        total_value = 0.0
        # PR Review: Use configured default price instead of hardcoded 10.0
        default_price = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)

        for item_id, qty in inventory.items():
            price = default_price
            if item_id in markets:
                m = markets[item_id]
                # Try various price attributes
                if hasattr(m, "avg_price") and m.avg_price > 0:
                    price = m.avg_price
                elif hasattr(m, "current_price") and m.current_price > 0:
                    price = m.current_price

            total_value += qty * price
        return total_value

    def _handle_agent_liquidation(self, state: SimulationState):
        """(기존 `_handle_agent_lifecycle` 로직 전체를 이 곳으로 이동)"""

        inactive_firms = [f for f in state.firms if not f.is_active]
        for firm in inactive_firms:
            self.logger.info(
                f"FIRM_LIQUIDATION | Starting liquidation for Firm {firm.id}. "
                f"Assets: {firm.assets:.2f}, Inventory: {sum(firm.inventory.values()):.2f}",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )

            # WO-106: Reflux Capture (Inventory & Capital)
            if state.reflux_system:
                # 1. Inventory Value
                inv_value = self._calculate_inventory_value(firm.inventory, state.markets)
                if inv_value > 0:
                    state.reflux_system.capture(inv_value, str(firm.id), "liquidation_inventory")
                    # FIX: Track Reflux Alchemy as Issuance
                    if hasattr(state.government, "total_money_issued"):
                        # MINTING: Inject value into Firm so it can be distributed
                        firm._add_assets(inv_value)
                        state.government.total_money_issued += inv_value

                # 2. Capital Stock (Scrap Value)
                if firm.capital_stock > 0:
                    state.reflux_system.capture(firm.capital_stock, str(firm.id), "liquidation_capital")
                    # FIX: Track Reflux Alchemy as Issuance
                    if hasattr(state.government, "total_money_issued"):
                        # MINTING: Inject value into Firm so it can be distributed
                        firm._add_assets(firm.capital_stock)
                        state.government.total_money_issued += firm.capital_stock

            # SoC Refactor: use hr.employees
            for employee in firm.hr.employees:
                if employee.is_active:
                    employee.is_employed = False
                    employee.employer_id = None
            firm.hr.employees = []
            firm.inventory.clear()
            firm.capital_stock = 0.0
            total_cash = firm.assets
            if total_cash > 0:
                outstanding_shares = firm.total_shares - firm.treasury_shares
                if outstanding_shares > 0:
                    # Fix: Include Inactive Households (pre-inheritance) and Government
                    shareholders = list(state.households)
                    if hasattr(state, 'government') and state.government:
                        shareholders.append(state.government)

                    for agent in shareholders:
                        # Check shares safely (Government might not have shares_owned init)
                        shares = 0
                        if hasattr(agent, "shares_owned"):
                            shares = agent.shares_owned.get(firm.id, 0)

                        if shares > 0:
                            share_ratio = shares / outstanding_shares
                            distribution = total_cash * share_ratio

                            # Use SettlementSystem for distribution
                            if hasattr(state, "settlement_system") and state.settlement_system:
                                state.settlement_system.transfer(firm, agent, distribution, "liquidation_dividend")
                            else:
                                raise RuntimeError("SettlementSystem missing during liquidation distribution")

                            self.logger.info(
                                f"LIQUIDATION_DISTRIBUTION | Agent {agent.id} received "
                                f"{distribution:.2f} from Firm {firm.id} liquidation",
                                extra={"agent_id": agent.id, "tags": ["liquidation"]}
                            )
                else:
                    from simulation.agents.government import Government
                    if isinstance(state.government, Government):
                        # Note: collect_tax no longer adds assets. We must transfer/add manually.
                        # Use SettlementSystem for Escheatment
                        if hasattr(state, "settlement_system") and state.settlement_system:
                            state.settlement_system.transfer(firm, state.government, total_cash, "liquidation_escheatment")
                        else:
                             raise RuntimeError("SettlementSystem missing during liquidation escheatment")

                        state.government.record_revenue(total_cash, "liquidation_escheatment", firm.id, state.time)

            # Verification: Firm assets should be ~0 now
            if firm.assets > 1e-6:
                 self.logger.warning(f"LIQUIDATION_RESIDUAL | Firm {firm.id} has {firm.assets} left after distribution. Forcing to 0.")
                 firm._sub_assets(firm.assets) # Destroy residual dust
                 if hasattr(state.government, "total_money_destroyed"):
                     state.government.total_money_destroyed += firm.assets

            for household in state.households:
                if firm.id in household.shares_owned:
                    del household.shares_owned[firm.id]
                    if state.stock_market:
                        state.stock_market.update_shareholder(household.id, firm.id, 0)
            self.logger.info(
                f"FIRM_LIQUIDATION_COMPLETE | Firm {firm.id} fully liquidated.",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )

        inactive_households = [h for h in state.households if not h.is_active]
        for household in inactive_households:
            # Use self.inheritance_manager since it is injected in __init__
            self.inheritance_manager.process_death(household, state.government, state)

            # WO-106: Reflux Capture (Household Inventory)
            if state.reflux_system:
                inv_value = self._calculate_inventory_value(household.inventory, state.markets)
                if inv_value > 0:
                    state.reflux_system.capture(inv_value, str(household.id), "liquidation_inventory")
                    # FIX: Track Reflux Alchemy as Issuance
                    if hasattr(state.government, "total_money_issued"):
                        # Minting to Government (Escheatment of dead inventory)
                        state.government._add_assets(inv_value)
                        state.government.total_money_issued += inv_value

            household.inventory.clear()
            household.shares_owned.clear()
            if hasattr(household, "portfolio"):
                 household.portfolio.holdings.clear()
            if state.stock_market:
                for firm_id in list(state.stock_market.shareholders.keys()):
                     state.stock_market.update_shareholder(household.id, firm_id, 0)

        # In-place modification to ensure references in WorldState are updated
        state.households[:] = [h for h in state.households if h.is_active]
        state.firms[:] = [f for f in state.firms if f.is_active]

        # Rebuild agents dict
        state.agents.clear()
        state.agents.update({agent.id: agent for agent in state.households + state.firms})
        if state.bank:
             state.agents[state.bank.id] = state.bank

        for firm in state.firms:
            # SoC Refactor: use hr.employees
            firm.hr.employees = [
                emp for emp in firm.hr.employees if emp.is_active and emp.id in state.agents
            ]
