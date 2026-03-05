from typing import Any, cast, Dict, Optional
from modules.finance.transaction.api import IAccountAccessor, InvalidAccountError, ITransactionParticipant, ITransactionValidator
from modules.finance.api import IFinancialAgent, IFinancialEntity
from modules.system.api import IAgentRegistry, CurrencyCode, DEFAULT_CURRENCY, ISystemFinancialAgent
import logging

logger = logging.getLogger(__name__)

class FinancialEntityAdapter:
    """
    Adapter for IFinancialEntity to ITransactionParticipant.
    """
    def __init__(self, entity: IFinancialEntity):
        self.entity = entity

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        self.entity.deposit(amount, currency)

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"ADAPTER_DEBUG | Entity {self.entity.id} Withdraw {amount}")
        self.entity.withdraw(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.entity.balance_pennies if currency == DEFAULT_CURRENCY else 0

    @property
    def allows_overdraft(self) -> bool:
        if isinstance(self.entity, ISystemFinancialAgent) and self.entity.is_system_agent():
            return True
        # Hardcoded ID check for Central Bank. IDs are usually int.
        from modules.system.constants import ID_CENTRAL_BANK
        return self.entity.id == ID_CENTRAL_BANK

class FinancialAgentAdapter:
    """
    Adapter for IFinancialAgent to ITransactionParticipant.
    """
    def __init__(self, agent: IFinancialAgent):
        self.agent = agent

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        self.agent._deposit(amount, currency)

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"ADAPTER_DEBUG | Agent {self.agent.id} Withdraw {amount}")
        self.agent._withdraw(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.agent.get_balance(currency)

    @property
    def allows_overdraft(self) -> bool:
        if isinstance(self.agent, ISystemFinancialAgent) and self.agent.is_system_agent():
            return True
        from modules.system.constants import ID_CENTRAL_BANK
        return self.agent.id == ID_CENTRAL_BANK


from modules.system.api import AgentID

class RegistryAccountAccessor(IAccountAccessor):
    def __init__(self, registry: IAgentRegistry):
        self.registry = registry
        # Dictionary to cache protocol check results: AgentClass -> ProtocolType (Agent/Entity/None)
        self._protocol_cache: Dict[type, str] = {}

    def _get_agent(self, account_id: AgentID) -> Any:
        try:
            agent = self.registry.get_agent(account_id)
            if agent: return agent
        except (KeyError, ValueError):
            pass

        return None

    def get_participant(self, account_id: AgentID) -> ITransactionParticipant:
        agent = self._get_agent(account_id)
        if agent is None:
            raise InvalidAccountError(f"Account (Agent) not found: {account_id}")

        agent_class = type(agent)
        if agent_class in self._protocol_cache:
            ptype = self._protocol_cache[agent_class]
            if ptype == 'agent': return FinancialAgentAdapter(agent)
            if ptype == 'entity': return FinancialEntityAdapter(agent)
        else:
            if isinstance(agent, IFinancialAgent):
                self._protocol_cache[agent_class] = 'agent'
                return FinancialAgentAdapter(agent)
            if isinstance(agent, IFinancialEntity):
                self._protocol_cache[agent_class] = 'entity'
                return FinancialEntityAdapter(agent)
            self._protocol_cache[agent_class] = 'none'

        raise InvalidAccountError(f"Agent {account_id} does not implement IFinancialAgent or IFinancialEntity.")

    def exists(self, account_id: AgentID) -> bool:
        agent = self._get_agent(account_id)
        if agent is None:
            return False

        agent_class = type(agent)
        if agent_class in self._protocol_cache:
            return self._protocol_cache[agent_class] in ('agent', 'entity')

        if isinstance(agent, IFinancialAgent):
            self._protocol_cache[agent_class] = 'agent'
            return True
        if isinstance(agent, IFinancialEntity):
            self._protocol_cache[agent_class] = 'entity'
            return True

        self._protocol_cache[agent_class] = 'none'
        return False

class DictionaryAccountAccessor(IAccountAccessor):
    """
    Accessor that uses a local dictionary of agents.
    Useful for testing or ad-hoc transactions where registry is not available.
    """
    def __init__(self, agents_map: Dict[AgentID, Any]):
        self.agents_map = agents_map
        self._protocol_cache: Dict[type, str] = {}

    def get_participant(self, account_id: AgentID) -> ITransactionParticipant:
        agent = self.agents_map.get(account_id)

        if agent is None:
            raise InvalidAccountError(f"Account (Agent) not found in local map: {account_id}")

        agent_class = type(agent)
        if agent_class in self._protocol_cache:
            ptype = self._protocol_cache[agent_class]
            if ptype == 'agent': return FinancialAgentAdapter(agent)
            if ptype == 'entity': return FinancialEntityAdapter(agent)
        else:
            if isinstance(agent, IFinancialAgent):
                self._protocol_cache[agent_class] = 'agent'
                return FinancialAgentAdapter(agent)
            if isinstance(agent, IFinancialEntity):
                self._protocol_cache[agent_class] = 'entity'
                return FinancialEntityAdapter(agent)
            self._protocol_cache[agent_class] = 'none'

        raise InvalidAccountError(f"Agent {account_id} does not implement protocols.")

    def exists(self, account_id: AgentID) -> bool:
        if account_id not in self.agents_map:
            return False

        agent = self.agents_map.get(account_id)
        if agent is None:
            return False

        agent_class = type(agent)
        if agent_class in self._protocol_cache:
            return self._protocol_cache[agent_class] in ('agent', 'entity')

        if isinstance(agent, IFinancialAgent):
            self._protocol_cache[agent_class] = 'agent'
            return True
        if isinstance(agent, IFinancialEntity):
            self._protocol_cache[agent_class] = 'entity'
            return True

        self._protocol_cache[agent_class] = 'none'
        return False
