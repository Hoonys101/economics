from typing import Any, TYPE_CHECKING, Dict
from modules.finance.api import IFinancialAgent, TaxCollectionResult
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.agents.government import Government

class GovernmentFiscalProxy(IFinancialAgent):
    """
    A restricted wrapper around the Government agent.
    Exposes only financial interface and tax collection capabilities
    to prevent unauthorized access to government internal state.
    """
    def __init__(self, government: "Government"):
        self._government = government

    @property
    def id(self) -> int:
        return self._government.id

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._government._deposit(amount, currency)

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._government._withdraw(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self._government.get_balance(currency)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return self._government.get_all_balances()

    @property
    def total_wealth(self) -> int:
        return self._government.total_wealth

    def collect_tax(self, amount: float, tax_type: str, payer: Any, current_tick: int) -> TaxCollectionResult:
        """
        Proxies the tax collection request to the government.
        """
        return self._government.collect_tax(amount, tax_type, payer, current_tick)
