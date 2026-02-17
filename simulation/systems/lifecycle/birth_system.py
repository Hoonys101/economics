from __future__ import annotations
from typing import List, Any, Optional
import logging
from simulation.systems.lifecycle.api import IBirthSystem
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.immigration_manager import ImmigrationManager
from simulation.systems.firm_management import FirmSystem
from modules.household.api import IHouseholdFactory
from simulation.finance.api import ISettlementSystem
from modules.system.api import ICurrencyHolder, DEFAULT_CURRENCY

class BirthSystem(IBirthSystem):
    """
    Handles creation of new agents via biological reproduction (Births),
    Immigration, and Entrepreneurship (Firm creation).
    """
    def __init__(self, config_module: Any,
                 demographic_manager: DemographicManager,
                 immigration_manager: ImmigrationManager,
                 firm_system: FirmSystem,
                 settlement_system: ISettlementSystem,
                 logger: logging.Logger,
                 household_factory: Optional[IHouseholdFactory] = None):
        self.config = config_module
        self.demographic_manager = demographic_manager
        self.immigration_manager = immigration_manager
        self.firm_system = firm_system
        self.settlement_system = settlement_system
        self.logger = logger
        self.household_factory = household_factory
        self.breeding_planner = VectorizedHouseholdPlanner(config_module)

    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Executes the birth phase.
        1. Process biological births.
        2. Process immigration.
        3. Check for new firm creation (Entrepreneurship).
        """
        # 3. Births
        new_children = self._process_births(state)
        self._register_new_agents(state, new_children)

        # 4. Immigration
        new_immigrants = self.immigration_manager.process_immigration(state)
        self._register_new_agents(state, new_immigrants)

        # 5. Entrepreneurship
        self.firm_system.check_entrepreneurship(state)

        return []

    def _process_births(self, state: SimulationState) -> List[Household]:
        if self.household_factory:
            # New Logic using Factory
            birth_requests = []
            active_households = [h for h in state.households if h._bio_state.is_active]
            if not active_households:
                return []

            decisions = self.breeding_planner.decide_breeding_batch(active_households)
            for h, decision in zip(active_households, decisions):
                if decision:
                    birth_requests.append(h)

            created_children = []
            for parent_agent in birth_requests:
                # Re-verify biological capability (sanity check)
                if not (self.config.REPRODUCTION_AGE_START <= parent_agent.age <= self.config.REPRODUCTION_AGE_END):
                    continue

                new_id = state.next_agent_id
                state.next_agent_id += 1

                # Asset Transfer Calculation
                parent_assets = 0
                if hasattr(parent_agent, 'wallet'):
                    parent_assets = parent_agent.wallet.get_balance(DEFAULT_CURRENCY)
                elif hasattr(parent_agent, 'assets') and isinstance(parent_agent.assets, dict):
                    parent_assets = int(parent_agent.assets.get(DEFAULT_CURRENCY, 0))
                elif hasattr(parent_agent, 'assets'): # Fallback
                     parent_assets = int(parent_agent.assets)

                initial_gift_pennies = int(max(0, min(parent_assets * 0.1, parent_assets)))

                try:
                    child = self.household_factory.create_newborn(
                        parent=parent_agent,
                        new_id=new_id,
                        initial_assets=initial_gift_pennies,
                        current_tick=state.time
                    )

                    parent_agent.children_ids.append(new_id)
                    created_children.append(child)

                    self.logger.info(
                        f"BIRTH | Parent {parent_agent.id} ({parent_agent.age:.1f}y) -> Child {child.id}. "
                        f"Assets: {initial_gift_pennies}",
                        extra={"parent_id": parent_agent.id, "child_id": child.id, "tick": state.time}
                    )
                except Exception as e:
                    self.logger.error(
                        f"BIRTH_FAILED | Failed to create child for parent {parent_agent.id}. Error: {e}",
                        extra={"parent_id": parent_agent.id, "error": str(e)}
                    )
                    continue
            return created_children
        else:
            # Fallback to legacy
            birth_requests = []
            active_households = [h for h in state.households if h._bio_state.is_active]
            if not active_households:
                return []

            decisions = self.breeding_planner.decide_breeding_batch(active_households)
            for h, decision in zip(active_households, decisions):
                if decision:
                    birth_requests.append(h)

            return self.demographic_manager.process_births(state, birth_requests)

    def _register_new_agents(self, state: SimulationState, new_agents: List[Household]):
        for agent in new_agents:
            state.households.append(agent)
            state.agents[agent.id] = agent
            agent.decision_engine.markets = state.markets
            agent.decision_engine.goods_data = state.goods_data

            # WO-218: Track new agent as currency holder for M2 integrity
            if isinstance(agent, ICurrencyHolder):
                state.register_currency_holder(agent)
            else:
                self.logger.critical(f"LIFECYCLE_ERROR | New Agent {agent.id} is NOT ICurrencyHolder!")

            # Ensure agent has settlement system
            if hasattr(agent, 'settlement_system'):
                agent.settlement_system = self.settlement_system

            if state.stock_market:
                for firm_id, holding in agent.portfolio.holdings.items():
                    state.stock_market.update_shareholder(agent.id, firm_id, holding.quantity)

            if state.ai_training_manager:
                state.ai_training_manager.agents.append(agent)
