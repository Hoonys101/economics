from typing import Optional, Any
import logging
from modules.finance.api import ILiquidityOracle, IFinancialEntity, IFinancialAgent
from modules.simulation.api import AgentID
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, IAgentRegistry, ICurrencyHolder
from modules.system.constants import NON_M2_SYSTEM_AGENT_IDS

logger = logging.getLogger(__name__)

class LiquidityOracle(ILiquidityOracle):
    """
    Tier 1 Implementation: Live Liquidity Oracle.
    Provides real-time, intra-tick balance and solvency checks for agents
    by interacting directly with the AgentRegistry and EstateRegistry.
    """

    def __init__(self, agent_registry: IAgentRegistry, estate_registry: Optional[Any] = None):
        self.agent_registry = agent_registry
        self.estate_registry = estate_registry

    def get_live_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Returns the current intra-tick balance of the agent in integer pennies.
        Delegates to the agent's live state via the registry.
        """
        try:
            agent = self._resolve_agent(agent_id)
            if not agent:
                # Agent not found (Dead/Removed)
                return 0

            # 1. Prefer IFinancialEntity for direct "pennies" access (Standard)
            if currency == DEFAULT_CURRENCY and isinstance(agent, IFinancialEntity):
                return agent.balance_pennies

            # 2. Fallback to IFinancialAgent (Legacy/Bank/Gov)
            if isinstance(agent, IFinancialAgent):
                return agent.get_balance(currency)

            # 3. Fallback to ICurrencyHolder (General)
            if isinstance(agent, ICurrencyHolder):
                return agent.get_assets_by_currency().get(currency, 0)

            return 0
        except Exception:
            # Swallow exceptions for robust querying, treating errors as zero balance
            return 0

    def check_solvency(self, agent_id: AgentID, required_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> bool:
        """
        Returns True if the agent has at least 'required_pennies'.
        Supports overdraft logic for System Agents if applicable.
        """
        # 1. System Agent Exemption (Soft Budget Constraint)
        # Note: Ideally, System Agents should be explicit, but we check ID list here for safety.
        if str(agent_id) in {str(uid) for uid in NON_M2_SYSTEM_AGENT_IDS}:
            return True

        agent = self._resolve_agent(agent_id)
        if not agent:
             return False

        # 2. Check actual balance
        current_balance = self.get_live_balance(agent_id, currency)
        return current_balance >= required_pennies

    def _resolve_agent(self, agent_id: AgentID) -> Optional[Any]:
        """Helper to resolve agent instance from primary or estate registry."""
        if self.agent_registry:
            agent = self.agent_registry.get_agent(agent_id)
            if agent:
                return agent

        if self.estate_registry:
            agent = self.estate_registry.get_agent(agent_id)
            if agent:
                return agent

        return None
