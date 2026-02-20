from typing import Any, cast, Dict, Optional
from modules.finance.transaction.api import IAccountAccessor, InvalidAccountError, ITransactionParticipant, ITransactionValidator
from modules.finance.api import IFinancialAgent, IFinancialEntity
from modules.system.api import IAgentRegistry, CurrencyCode, DEFAULT_CURRENCY

class FinancialEntityAdapter:
    """
    Adapter for IFinancialEntity to ITransactionParticipant.
    """
    def __init__(self, entity: IFinancialEntity):
        self.entity = entity

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        self.entity.deposit(amount, currency)

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        self.entity.withdraw(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.entity.balance_pennies if currency == DEFAULT_CURRENCY else 0

    @property
    def allows_overdraft(self) -> bool:
        # Hardcoded ID check for Central Bank. IDs are usually int.
        from modules.system.constants import ID_CENTRAL_BANK
        return self.entity.id == ID_CENTRAL_BANK or str(self.entity.id) == str(ID_CENTRAL_BANK)

class FinancialAgentAdapter:
    """
    Adapter for IFinancialAgent to ITransactionParticipant.
    """
    def __init__(self, agent: IFinancialAgent):
        self.agent = agent

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        self.agent._deposit(amount, currency)

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        self.agent._withdraw(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.agent.get_balance(currency)

    @property
    def allows_overdraft(self) -> bool:
        from modules.system.constants import ID_CENTRAL_BANK
        return self.agent.id == ID_CENTRAL_BANK or str(self.agent.id) == str(ID_CENTRAL_BANK)


class RegistryAccountAccessor(IAccountAccessor):
    def __init__(self, registry: IAgentRegistry):
        self.registry = registry

    def _get_agent(self, account_id: str) -> Any:
        # 1. Try as Int (Common Case)
        if isinstance(account_id, str) and account_id.isdigit():
            try:
                agent = self.registry.get_agent(int(account_id))
                if agent: return agent
            except (KeyError, ValueError):
                pass

        # 2. Try as String (Fallback or Non-Numeric ID)
        try:
            agent = self.registry.get_agent(account_id)
            if agent: return agent
        except (KeyError, ValueError):
            pass

        return None

    def get_participant(self, account_id: str) -> ITransactionParticipant:
        agent = self._get_agent(account_id)
        if agent is None:
            raise InvalidAccountError(f"Account (Agent) not found: {account_id}")

        # Check IFinancialAgent first as it supports multi-currency balance check better
        if isinstance(agent, IFinancialAgent):
            return FinancialAgentAdapter(agent)

        if isinstance(agent, IFinancialEntity):
            return FinancialEntityAdapter(agent)

        raise InvalidAccountError(f"Agent {account_id} does not implement IFinancialAgent or IFinancialEntity.")

    def exists(self, account_id: str) -> bool:
        agent = self._get_agent(account_id)
        return agent is not None and (
            isinstance(agent, IFinancialAgent) or
            isinstance(agent, IFinancialEntity)
        )

class DictionaryAccountAccessor(IAccountAccessor):
    """
    Accessor that uses a local dictionary of agents.
    Useful for testing or ad-hoc transactions where registry is not available.
    """
    def __init__(self, agents_map: Dict[str, Any]):
        self.agents_map = agents_map

    def get_participant(self, account_id: str) -> ITransactionParticipant:
        agent = self.agents_map.get(account_id)
        if agent is None:
             # Try int key
             if account_id.isdigit():
                 agent = self.agents_map.get(int(account_id))

        if agent is None:
            raise InvalidAccountError(f"Account (Agent) not found in local map: {account_id}")

        if isinstance(agent, IFinancialAgent):
            return FinancialAgentAdapter(agent)
        if isinstance(agent, IFinancialEntity):
            return FinancialEntityAdapter(agent)

        raise InvalidAccountError(f"Agent {account_id} does not implement protocols.")

    def exists(self, account_id: str) -> bool:
        return (account_id in self.agents_map) or (account_id.isdigit() and int(account_id) in self.agents_map)
