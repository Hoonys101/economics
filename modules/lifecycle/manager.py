import logging
from typing import Any, Dict, Protocol, List
from modules.lifecycle.api import IAgentLifecycleManager, AgentRegistrationDTO, AgentDeactivationEventDTO, LifecycleEventType
from modules.system.api import IAgentRegistry, AgentID, IAgent, IAssetRecoverySystem
from modules.finance.api import IMonetaryLedger

class ISagaOrchestrator(Protocol):
    def cancel_all_sagas_for_agent(self, agent_id: AgentID) -> None:
        ...

class IMarketSystem(Protocol):
    def cancel_all_orders_for_agent(self, agent_id: AgentID) -> None:
        ...

class AgentRegistrationException(Exception):
    pass

class IAgentFactory(Protocol):
    def create(self, agent_id: AgentID, dto: AgentRegistrationDTO) -> Any:
        ...

class AgentLifecycleManager(IAgentLifecycleManager):
    def __init__(self,
                 agent_registry: IAgentRegistry,
                 monetary_ledger: IMonetaryLedger,
                 saga_orchestrator: ISagaOrchestrator,
                 market_system: IMarketSystem,
                 asset_recovery_system: IAssetRecoverySystem,
                 logger: logging.Logger,
                 firm_factory: IAgentFactory = None,
                 household_factory: IAgentFactory = None):
        self.registry = agent_registry
        self.ledger = monetary_ledger
        self.saga_orchestrator = saga_orchestrator
        self.market_system = market_system
        self.asset_recovery_system = asset_recovery_system
        self.logger = logger
        self.firm_factory = firm_factory
        self.household_factory = household_factory
        self._next_id = 1000 # Dummy ID allocator for now if registry doesn't provide one

    def register_firm(self, dto: AgentRegistrationDTO) -> AgentID:
        try:
            # 1. Allocate ID and create firm object
            # (Assuming a simple factory approach or getting ID from registry)
            new_id = self._next_id
            self._next_id += 1

            # create_firm(...)
            firm_entity = self.firm_factory.create(new_id, dto) if self.firm_factory else None

            if not firm_entity:
                raise AgentRegistrationException("Firm factory not provided or failed.")

            # ATOMIC TRANSACTION START
            self.registry.register(firm_entity)

            # Initial assets to pennies
            cash_amount = dto.initial_assets.get("cash", 0)

            # Create account - not strictly in ledger API directly right now, might just be giving them money?
            # Assuming ledger requires an account or we just update M2 expectations
            self.ledger.record_monetary_expansion(cash_amount, "FIRM_REGISTRATION")
            # In a full system, you'd add the money to the firm's wallet.

            self.logger.info(f"Firm {new_id} registered atomically.")
            return new_id

        except Exception as e:
            # Rollback registry
            # We don't have a formal rollback in IAgentRegistry, so we might need a workaround or add it.
            self.logger.error(f"Failed to register firm: {e}")
            raise AgentRegistrationException(str(e))

    def register_household(self, dto: AgentRegistrationDTO) -> AgentID:
        try:
            new_id = self._next_id
            self._next_id += 1

            household_entity = self.household_factory.create(new_id, dto) if self.household_factory else None

            if not household_entity:
                raise AgentRegistrationException("Household factory not provided or failed.")

            self.registry.register(household_entity)

            cash_amount = dto.initial_assets.get("cash", 0)
            self.ledger.record_monetary_expansion(cash_amount, "HOUSEHOLD_REGISTRATION")

            self.logger.info(f"Household {new_id} registered atomically.")
            return new_id

        except Exception as e:
            self.logger.error(f"Failed to register household: {e}")
            raise AgentRegistrationException(str(e))

    def deactivate_agent(self, agent_id: AgentID, reason: LifecycleEventType, current_tick: int) -> AgentDeactivationEventDTO:
        # 1. Fetch agent
        agent = self.registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found in registry.")

        # 2. Set inactive
        # No formal 'set_inactive' on registry, we might mutate the agent or registry
        if hasattr(agent, "is_active"):
            agent.is_active = False

        # 3. Cancel Sagas
        self.saga_orchestrator.cancel_all_sagas_for_agent(agent_id)

        # 4. Cancel Orders
        self.market_system.cancel_all_orders_for_agent(agent_id)

        # 5. Asset Recovery / Bankruptcy
        # (Mocking unresolved liabilities as 0 for now)
        liabilities = 0

        return AgentDeactivationEventDTO(
            agent_id=agent_id,
            reason=reason,
            tick=current_tick,
            unresolved_liabilities=liabilities
        )

    def process_starvation(self, household_id: AgentID, current_tick: int) -> None:
        agent = self.registry.get_agent(household_id)
        if not agent:
            return

        if hasattr(agent, "needs"):
            survival = agent.needs.get("survival", 100.0)
            if survival <= 0:
                self.deactivate_agent(household_id, LifecycleEventType.STARVED, current_tick)
