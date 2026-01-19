# simulation/systems/lifecycle_manager.py

from __future__ import annotations
from typing import List, TYPE_CHECKING, Any
import logging

if TYPE_CHECKING:
    from simulation.engine import Simulation
    from simulation.core_agents import Household

from simulation.systems.api import AgentLifecycleManagerInterface
from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.immigration_manager import ImmigrationManager
from simulation.systems.inheritance_manager import InheritanceManager
from simulation.systems.firm_management import FirmSystem
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner

class AgentLifecycleManager(AgentLifecycleManagerInterface):
    """에이전트의 생성, 노화, 사망, 청산을 처리합니다."""

    def __init__(self, config_module: Any, demographic_manager: DemographicManager,
                 inheritance_manager: InheritanceManager, firm_system: FirmSystem, logger: logging.Logger):
        self.config = config_module
        self.demographic_manager = demographic_manager
        self.inheritance_manager = inheritance_manager
        self.firm_system = firm_system
        self.immigration_manager = ImmigrationManager(config_module=config_module)
        self.breeding_planner = VectorizedHouseholdPlanner(config_module)
        self.logger = logger

    def process_lifecycle_events(self, sim: Simulation):
        """한 틱 동안 발생하는 모든 생명주기 관련 이벤트를 처리합니다."""

        # 1. Aging
        self.demographic_manager.process_aging(sim.households, sim.time)

        # 2. Births (출생)
        new_children = self._process_births(sim)
        self._register_new_agents(sim, new_children)

        # 3. Immigration (이민)
        new_immigrants = self.immigration_manager.process_immigration(sim)
        self._register_new_agents(sim, new_immigrants)

        # 4. Entrepreneurship (창업) - FirmSystem과 협력
        self.firm_system.check_entrepreneurship(sim)

        # 5. Death & Liquidation (사망 및 청산)
        self._handle_agent_liquidation(sim)

    def _process_births(self, sim: Simulation) -> List[Household]:
        """(기존 `run_tick`의 출생 로직)"""
        from simulation.core_agents import Household
        birth_requests = []
        # Ensure only households are processed
        active_households = [h for h in sim.households if h.is_active and isinstance(h, Household)]
        if not active_households:
            return []

        decisions = self.breeding_planner.decide_breeding_batch(active_households)
        for h, decision in zip(active_households, decisions):
            if decision:
                birth_requests.append(h)

        return self.demographic_manager.process_births(sim, birth_requests)

    def _register_new_agents(self, sim: Simulation, new_agents: List[Household]):
        """(기존 `run_tick`의 신규 에이전트 등록 로직)"""
        for agent in new_agents:
            sim.households.append(agent)
            sim.agents[agent.id] = agent
            agent.decision_engine.markets = sim.markets
            agent.decision_engine.goods_data = sim.goods_data

            if sim.stock_market:
                for firm_id, qty in agent.shares_owned.items():
                    sim.stock_market.update_shareholder(agent.id, firm_id, qty)

    def _handle_agent_liquidation(self, sim: Simulation):
        """(기존 `_handle_agent_lifecycle` 로직 전체를 이 곳으로 이동)"""

        inactive_firms = [f for f in sim.firms if not f.is_active]
        for firm in inactive_firms:
            self.logger.info(
                f"FIRM_LIQUIDATION | Starting liquidation for Firm {firm.id}. "
                f"Assets: {firm.assets:.2f}, Inventory: {sum(firm.inventory.values()):.2f}",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )
            for employee in firm.employees:
                if employee.is_active:
                    employee.is_employed = False
                    employee.employer_id = None
            firm.employees = []
            firm.inventory.clear()
            firm.capital_stock = 0.0
            total_cash = firm.assets
            if total_cash > 0:
                outstanding_shares = firm.total_shares - firm.treasury_shares
                if outstanding_shares > 0:
                    for household in sim.households:
                        if household.is_active and firm.id in household.shares_owned:
                            share_ratio = household.shares_owned[firm.id] / outstanding_shares
                            distribution = total_cash * share_ratio
                            household.assets += distribution
                            self.logger.info(
                                f"LIQUIDATION_DISTRIBUTION | Household {household.id} received "
                                f"{distribution:.2f} from Firm {firm.id} liquidation",
                                extra={"agent_id": household.id, "tags": ["liquidation"]}
                            )
                else:
                    from simulation.agents.government import Government
                    if isinstance(sim.government, Government):
                        sim.government.collect_tax(total_cash, "liquidation_escheatment", firm.id, sim.time)
            for household in sim.households:
                if firm.id in household.shares_owned:
                    del household.shares_owned[firm.id]
                    if sim.stock_market:
                        sim.stock_market.update_shareholder(household.id, firm.id, 0)
            firm.assets = 0.0
            self.logger.info(
                f"FIRM_LIQUIDATION_COMPLETE | Firm {firm.id} fully liquidated.",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )

        inactive_households = [h for h in sim.households if not h.is_active]
        for household in inactive_households:
            # Check if it is really a Household, not Firm (just in case list corruption)
            if not hasattr(household, "portfolio"):
                continue

            if hasattr(sim, "inheritance_manager"):
                sim.inheritance_manager.process_death(household, sim.government, sim)

            household.inventory.clear()
            # Check if shares_owned exists (legacy)
            if hasattr(household, "shares_owned"):
                household.shares_owned.clear()

            if hasattr(household, "portfolio") and hasattr(household.portfolio, "holdings"):
                household.portfolio.holdings.clear()
            if sim.stock_market:
                for firm_id in list(sim.stock_market.shareholders.keys()):
                     sim.stock_market.update_shareholder(household.id, firm_id, 0)

        sim.households = [h for h in sim.households if h.is_active]
        sim.firms = [f for f in sim.firms if f.is_active]

        sim.agents = {agent.id: agent for agent in sim.households + sim.firms}
        sim.agents[sim.bank.id] = sim.bank

        for firm in sim.firms:
            firm.employees = [
                emp for emp in firm.employees if emp.is_active and emp.id in sim.agents
            ]
