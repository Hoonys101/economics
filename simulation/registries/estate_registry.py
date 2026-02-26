from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging

from modules.simulation.api import AgentID, IAgent
from modules.system.constants import ID_PUBLIC_MANAGER, ID_GOVERNMENT
from modules.finance.api import IFinancialEntity, IFinancialAgent

if TYPE_CHECKING:
    from modules.finance.api import ISettlementSystem
    from simulation.models import Transaction

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

    def process_estate_distribution(self, agent: IAgent, settlement_system: 'ISettlementSystem') -> List[Transaction]:
        """
        Distributes assets of the dead agent.
        Priority: Taxes -> Creditors -> Heirs -> Escheatment (Government).

        This method is called POST-EXECUTION of an incoming transfer, so funds
        are already in the dead agent's account.

        Returns:
            List[Transaction]: A list of transactions generated during distribution.
        """
        transactions = []

        # 1. Type Check & Balance Retrieval
        current_balance = 0

        # Prefer IFinancialEntity for standardized balance access
        if isinstance(agent, IFinancialEntity):
            current_balance = agent.balance_pennies
        elif isinstance(agent, IFinancialAgent):
            current_balance = agent.get_balance()
        else:
            # Fallback/Duck typing (discouraged but defensive)
            if hasattr(agent, 'balance_pennies'):
                current_balance = agent.balance_pennies
            elif hasattr(agent, 'get_balance'):
                current_balance = agent.get_balance()

        if current_balance <= 0:
            return transactions

        logger.info(f"ESTATE_PROCESS: distributing {current_balance} from Agent {agent.id}")

        # 2. Heir Logic (Household)
        children_ids = getattr(agent, 'children_ids', [])
        distributed = False

        if children_ids:
            # Pay first child
            heir_id = children_ids[0]

            # Use settlement_system.agent_registry to fetch heir (must be active)
            if settlement_system.agent_registry:
                heir = settlement_system.agent_registry.get_agent(heir_id)
                if heir:
                    logger.info(f"ESTATE_DISTRIBUTE: Transferring {current_balance} to Heir {heir_id}")
                    # Note: We must ensure 'agent' (the dead one) is compatible with transfer
                    # Assuming IFinancialEntity/Agent
                    tx = settlement_system.transfer(
                        debit_agent=agent, # The dead agent
                        credit_agent=heir,
                        amount=current_balance,
                        memo="inheritance_distribution"
                    )
                    if tx:
                        transactions.append(tx)
                    distributed = True
                else:
                    logger.warning(f"ESTATE_DISTRIBUTE: Heir {heir_id} not found/active.")

        # 3. Fallback: Escheatment to Government
        if not distributed:
            escheat_txs = self._escheat_to_government(agent, current_balance, settlement_system)
            transactions.extend(escheat_txs)

        return transactions

    def _escheat_to_government(self, agent: IAgent, amount: int, settlement_system: 'ISettlementSystem') -> List[Transaction]:
        """Transfers unclaimed assets to the Public Manager/Government."""
        transactions = []
        if not settlement_system.agent_registry:
            logger.error("ESTATE_ESCHEAT_FAIL: No agent registry available.")
            return transactions

        # Try to find Public Manager or Government
        gov_agent = settlement_system.agent_registry.get_agent(ID_PUBLIC_MANAGER)
        if not gov_agent:
             # Fallback to ID_GOVERNMENT
             gov_agent = settlement_system.agent_registry.get_agent(ID_GOVERNMENT)

        if gov_agent:
            logger.info(f"ESTATE_ESCHEAT: Transferring {amount} from {agent.id} to Government/PublicManager {gov_agent.id}")
            tx = settlement_system.transfer(
                debit_agent=agent,
                credit_agent=gov_agent,
                amount=amount,
                memo="escheatment"
            )
            if tx:
                transactions.append(tx)
        else:
            logger.error("ESTATE_ESCHEAT_FAIL: PublicManager/Government agent not found.")

        return transactions
