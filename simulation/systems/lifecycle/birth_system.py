from __future__ import annotations
from typing import List, Any, Optional, Tuple, cast
import logging
from simulation.systems.lifecycle.api import IBirthSystem, BirthConfigDTO
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
from simulation.systems.demographic_manager import DemographicManager
from simulation.systems.immigration_manager import ImmigrationManager
from simulation.systems.firm_management import FirmSystem
from modules.household.api import IHouseholdFactory
from simulation.finance.api import ISettlementSystem
from modules.system.api import ICurrencyHolder, DEFAULT_CURRENCY, IAgentRegistry

class BirthSystem(IBirthSystem):
    """
    Handles creation of new agents via biological reproduction (Births),
    Immigration, and Entrepreneurship (Firm creation).
    Adheres to Sacred Sequence by returning transactions for execution.
    """
    def __init__(self, config: BirthConfigDTO,
                 breeding_planner: VectorizedHouseholdPlanner,
                 demographic_manager: DemographicManager,
                 immigration_manager: ImmigrationManager,
                 firm_system: FirmSystem,
                 settlement_system: ISettlementSystem,
                 logger: logging.Logger,
                 household_factory: IHouseholdFactory): # Mandatory
        self.config = config
        self.breeding_planner = breeding_planner
        self.demographic_manager = demographic_manager
        self.immigration_manager = immigration_manager
        self.firm_system = firm_system
        self.settlement_system = settlement_system
        self.logger = logger
        if household_factory is None:
             raise ValueError("IHouseholdFactory is mandatory for BirthSystem.")
        self.household_factory = household_factory

    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Executes the birth phase.
        1. Process biological births.
        2. Process immigration.
        3. Check for new firm creation (Entrepreneurship).
        """
        all_transactions = []

        # 3. Births
        new_children, birth_txs = self._process_births(state)
        self._register_new_agents(state, new_children)
        all_transactions.extend(birth_txs)

        # 4. Immigration
        new_immigrants = self.immigration_manager.process_immigration(state)
        self._register_new_agents(state, new_immigrants)

        # 5. Entrepreneurship
        self.firm_system.check_entrepreneurship(state)

        return all_transactions

    def _process_births(self, state: SimulationState) -> Tuple[List[Household], List[Transaction]]:
        birth_requests = []
        # Use Protocol property if available, otherwise assume Household object has is_active
        active_households = [h for h in state.households if h.is_active]
        if not active_households:
            return [], []

        decisions = self.breeding_planner.decide_breeding_batch(active_households)
        for h, decision in zip(active_households, decisions):
            if decision:
                birth_requests.append(h)

        created_children = []
        transactions = []

        for parent_agent in birth_requests:
            # Re-verify biological capability (sanity check)
            if not (self.config.reproduction_age_start <= parent_agent.age <= self.config.reproduction_age_end):
                continue

            new_id = state.next_agent_id
            state.next_agent_id += 1

            # Asset Transfer Calculation
            parent_assets = 0
            if isinstance(parent_agent, ICurrencyHolder):
                parent_assets = parent_agent.get_balance(DEFAULT_CURRENCY)

            initial_gift_pennies = int(max(0, min(parent_assets * 0.1, parent_assets)))

            try:
                # Pass initial_assets=0 to factory to prevent it from handling transfer.
                # We will handle it explicitly via Transaction for Sacred Sequence.
                child = self.household_factory.create_newborn(
                    parent=parent_agent,
                    new_id=new_id,
                    initial_assets=0,
                    current_tick=state.time
                )

                # Explicit Zero-Sum Transfer Transaction
                if initial_gift_pennies > 0:
                     tx = Transaction(
                         buyer_id=parent_agent.id,
                         seller_id=child.id,
                         item_id="BIRTH_GIFT",
                         quantity=1.0,
                         price=float(initial_gift_pennies) / 100.0,
                         total_pennies=initial_gift_pennies,
                         market_id="settlement",
                         transaction_type="GIFT",
                         time=state.time,
                         currency=DEFAULT_CURRENCY
                     )
                     transactions.append(tx)

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

        return created_children, transactions

    def _register_new_agents(self, state: SimulationState, new_agents: List[Household]):
        for agent in new_agents:
            state.households.append(agent)
            state.agents[agent.id] = agent

            # Setup dependencies
            # Agent is guaranteed to be Household
            agent.decision_engine.markets = state.markets
            agent.decision_engine.goods_data = state.goods_data

            # WO-218: Track new agent as currency holder for M2 integrity
            if state.currency_registry_handler:
                state.currency_registry_handler.register_currency_holder(agent)
            elif state.currency_holders is not None:
                state.currency_holders.append(agent)

            # Ensure agent has settlement system
            # Dynamic injection for systems that need it (e.g. HousingConnector)
            # We set it blindly as Household instance allows dynamic attributes
            agent.settlement_system = self.settlement_system

            # Shareholder Registry sync
            if state.shareholder_registry:
                 # No shares initially for newborn
                 pass
            elif state.stock_market:
                # Handle potential portfolio from immigrants (newborns have empty portfolio)
                for firm_id, holding in agent.portfolio.holdings.items():
                    # We check for update_shareholder availability on stock_market
                    # because stock_market is Optional[Any] in state
                    if hasattr(state.stock_market, 'update_shareholder'):
                         state.stock_market.update_shareholder(agent.id, firm_id, holding.quantity)

            if state.ai_training_manager:
                state.ai_training_manager.agents.append(agent)
