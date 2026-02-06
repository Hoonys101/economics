from typing import Any, Dict, Union
import logging
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.finance.api import IFinancialEntity
from modules.finance.api import InsufficientFundsError

logger = logging.getLogger(__name__)

class FinancialEntityAdapter(IFinancialEntity):
    """
    Adapter pattern to treat legacy agents (Households, Firms, Government, etc.)
    as strict IFinancialEntity objects.

    Encapsulates the heterogeneity of asset storage (Wallet vs Finance vs EconState vs Assets).
    """

    def __init__(self, agent: Any):
        self._agent = agent
        self.id = getattr(agent, 'id', -1)

    @property
    def assets(self) -> float:
        """
        Returns the balance in DEFAULT_CURRENCY.
        """
        return self.get_balance(DEFAULT_CURRENCY)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        agent = self._agent

        # 1. Wallet (Modern Standard)
        if hasattr(agent, 'wallet') and agent.wallet is not None:
            return agent.wallet.get_balance(currency)

        # 2. Firm Finance (Legacy)
        if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
            raw_balance = agent.finance.balance
            return self._extract_currency_value(raw_balance, currency)

        # 3. Household EconState (Legacy)
        if hasattr(agent, '_econ_state') and hasattr(agent._econ_state, 'assets'):
            raw_balance = agent._econ_state.assets
            return self._extract_currency_value(raw_balance, currency)

        # 4. Direct Assets Property (Legacy / Simple Agents)
        if hasattr(agent, 'assets'):
            raw_balance = agent.assets
            return self._extract_currency_value(raw_balance, currency)

        return 0.0

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        agent = self._agent

        # 1. Standard deposit method (Preferred)
        if hasattr(agent, 'deposit'):
            # Check signature or just try calling
            try:
                # Some agents might accept currency, others might not
                # Inspecting signature is hard at runtime effectively without overhead.
                # We assume if it has 'wallet', 'deposit' supports currency.
                if hasattr(agent, 'wallet') and agent.wallet is not None:
                    agent.deposit(amount, currency=currency)
                    return
            except TypeError:
                # Fallback to single argument
                pass

            # Try single arg
            try:
                agent.deposit(amount)
                return
            except TypeError:
                 pass

        # 2. Manual Update (If no deposit method)
        # This is risky but matches legacy direct access if needed.
        # However, most agents HAVE a deposit method.
        # If not, we fall back to property setting if possible, but that's dangerous.

        # Re-using get logic to find WHERE to deposit
        if hasattr(agent, 'wallet') and agent.wallet is not None:
             agent.wallet.deposit(amount, currency)
             return

        if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
             # Firm finance typically has credit/deposit methods
             if hasattr(agent.finance, 'credit'):
                 agent.finance.credit(amount, "Deposit", currency=currency)
                 return
             # Direct dict manipulation
             if isinstance(agent.finance.balance, dict):
                 agent.finance.balance[currency] = agent.finance.balance.get(currency, 0.0) + amount
             else:
                 agent.finance.balance += amount
             return

        if hasattr(agent, '_econ_state') and hasattr(agent._econ_state, 'assets'):
             if isinstance(agent._econ_state.assets, dict):
                 agent._econ_state.assets[currency] = agent._econ_state.assets.get(currency, 0.0) + amount
             else:
                 agent._econ_state.assets += amount
             return

        if hasattr(agent, 'assets'):
             if isinstance(agent.assets, dict):
                 agent.assets[currency] = agent.assets.get(currency, 0.0) + amount
             else:
                 # Assuming float
                 agent.assets += amount
             return

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount < 0:
             raise ValueError("Cannot withdraw negative amount")

        current = self.get_balance(currency)
        if current < amount:
             raise InsufficientFundsError(f"Agent {self.id} has {current} {currency}, needed {amount}")

        agent = self._agent

        # 1. Standard withdraw method (Preferred)
        if hasattr(agent, 'withdraw'):
            try:
                if hasattr(agent, 'wallet') and agent.wallet is not None:
                    agent.withdraw(amount, currency=currency)
                    return
            except TypeError:
                pass

            try:
                agent.withdraw(amount)
                return
            except TypeError:
                pass

        # 2. Manual Update
        if hasattr(agent, 'wallet') and agent.wallet is not None:
             agent.wallet.withdraw(amount, currency)
             return

        if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
             if hasattr(agent.finance, 'debit'):
                 agent.finance.debit(amount, "Withdrawal", currency=currency)
                 return
             if isinstance(agent.finance.balance, dict):
                 agent.finance.balance[currency] -= amount
             else:
                 agent.finance.balance -= amount
             return

        if hasattr(agent, '_econ_state') and hasattr(agent._econ_state, 'assets'):
             if isinstance(agent._econ_state.assets, dict):
                 agent._econ_state.assets[currency] -= amount
             else:
                 agent._econ_state.assets -= amount
             return

        if hasattr(agent, 'assets'):
             if isinstance(agent.assets, dict):
                 agent.assets[currency] -= amount
             else:
                 agent.assets -= amount
             return

    def _extract_currency_value(self, assets_raw: Union[float, Dict[str, float]], currency: CurrencyCode) -> float:
        if isinstance(assets_raw, dict):
            return assets_raw.get(currency, 0.0)
        try:
            return float(assets_raw)
        except (ValueError, TypeError):
            return 0.0
