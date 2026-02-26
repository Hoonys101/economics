from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging

from modules.simulation.api import AgentID, IAgent
from simulation.models import Transaction
from modules.finance.transaction.api import TransactionResultDTO

if TYPE_CHECKING:
    from modules.finance.api import ISettlementSystem, ILiquidatable, IFinancialAgent

logger = logging.getLogger(__name__)

class EstateRegistry:
    """
    Registry for managing agents that have been liquidated or are deceased (The Estate).
    Maintains a record of agents removed from the active AgentRegistry to allow
    final financial settlements (escheatment, tax, dividends) to complete.
    """
    def __init__(self) -> None:
        self._estate: Dict[AgentID, IAgent] = {}

    def add_to_estate(self, agent: IAgent) -> None:
        """Moves an agent to the estate registry."""
        if agent and hasattr(agent, 'id'):
             self._estate[agent.id] = agent
             logger.info(f"ESTATE: Agent {agent.id} added to Estate Registry.")

    def get_agent(self, agent_id: Any) -> Optional[IAgent]:
        """Retrieves an agent from the estate."""
        # Handle int/str conversion if necessary, similar to AgentRegistry
        if agent_id in self._estate:
            return self._estate[agent_id]

        # Try casting to int if string
        if isinstance(agent_id, str) and agent_id.isdigit():
             return self._estate.get(int(agent_id))

        # Try casting to int if it's a number (but not int? unlikely for AgentID)
        try:
            return self._estate.get(int(agent_id))
        except (ValueError, TypeError):
            pass

        return None

    def get_all_estate_agents(self) -> List[IAgent]:
        """Returns all agents currently in the estate."""
        return list(self._estate.values())

    def intercept_transaction(self, tx: Transaction, settlement_system: 'ISettlementSystem') -> Optional[Transaction]:
        """
        Intercepts a transaction destined for a dead agent.
        1. Executes the original transfer (to the estate agent) forcefully.
        2. Triggers simplified distribution logic (Heir/Escheatment).

        Returns the executed transaction if successful.
        """
        dead_agent_id = tx.receiver_id
        dead_agent = self.get_agent(dead_agent_id)

        if not dead_agent:
            logger.error(f"ESTATE_INTERCEPT_FAIL: Agent {dead_agent_id} not found in estate.")
            return None

        logger.info(f"ESTATE_INTERCEPT: Processing transaction {tx.total_pennies} -> Dead Agent {dead_agent_id}")

        # 1. Force Execute the Original Transfer (Sender -> Dead Agent)
        # We use the lower-level engine to bypass SettlementSystem's recursive check
        engine = settlement_system._get_engine(context_agents=[])

        # Note: We rely on the engine's validation or assume sender has funds (SettlementSystem checked seamless funds)
        result_dto = engine.process_transaction(
            source_account_id=str(tx.sender_id),
            destination_account_id=str(dead_agent_id),
            amount=tx.total_pennies,
            currency=tx.currency,
            description=f"Estate Intercept: {tx.memo or ''}"
        )

        if result_dto.status != 'COMPLETED':
            logger.error(f"ESTATE_INTERCEPT_FAIL: Engine execution failed: {result_dto.message}")
            return None

        # 2. Trigger Distribution
        self._distribute_assets(dead_agent, settlement_system)

        # Return the original transaction (now executed)
        tx.metadata = tx.metadata or {}
        tx.metadata['intercepted'] = True
        return tx

    def _distribute_assets(self, agent: IAgent, settlement_system: 'ISettlementSystem') -> None:
        """
        Distributes assets of the dead agent.
        Priority: Taxes -> Creditors -> Heirs.
        """
        # Simplified Logic for Phase 1
        # 1. Check if Household and has heirs
        # We need to cast to access attributes safely or use getattr

        # Check balance
        current_balance = 0
        if hasattr(agent, 'balance_pennies'):
            current_balance = agent.balance_pennies
        elif hasattr(agent, 'get_balance'):
            current_balance = agent.get_balance()

        if current_balance <= 0:
            return

        # Simple Heir Logic (Household)
        children_ids = getattr(agent, 'children_ids', [])
        if children_ids:
            # Pay first child
            heir_id = children_ids[0]
            # Verify heir exists? SettlementSystem.transfer will check.
            # But heir needs to be an IFinancialAgent.
            # We assume active registry handles getting the heir.

            # We can't fetch the heir object here easily without active registry access.
            # SettlementSystem.transfer needs OBJECTS.
            # If we pass objects, we need to fetch them.

            # Use settlement_system.agent_registry to fetch heir
            if settlement_system.agent_registry:
                heir = settlement_system.agent_registry.get_agent(heir_id)
                if heir:
                    logger.info(f"ESTATE_DISTRIBUTE: Transferring {current_balance} to Heir {heir_id}")
                    settlement_system.transfer(
                        debit_agent=agent, # The dead agent
                        credit_agent=heir,
                        amount=current_balance,
                        memo="inheritance_distribution"
                    )
                else:
                    logger.warning(f"ESTATE_DISTRIBUTE: Heir {heir_id} not found/active.")
        else:
            # Escheatment to Government?
            # Need access to Gov agent.
            # SettlementSystem might have access via agent_registry or hardcoded ID.
            pass
