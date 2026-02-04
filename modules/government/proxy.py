from typing import Any, TYPE_CHECKING, Dict
from modules.finance.api import IFinancialEntity, TaxCollectionResult
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.agents.government import Government

class GovernmentFiscalProxy(IFinancialEntity):
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

    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        return self._government.assets

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._government.deposit(amount, currency)

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._government.withdraw(amount, currency)

    def collect_tax(self, amount: float, tax_type: str, payer: Any, current_tick: int) -> TaxCollectionResult:
        """
        Proxies the tax collection request to the government.
        """
        return self._government.collect_tax(amount, tax_type, payer, current_tick)
