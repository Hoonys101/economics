from _typeshed import Incomplete
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Any

logger: Incomplete

class CurrencyExchangeEngine:
    """
    Handles currency exchange rate retrieval and conversion.
    Reads parity configuration from config/simulation.yaml.
    """
    config_module: Incomplete
    def __init__(self, config_module: Any) -> None: ...
    def get_exchange_rate(self, currency: CurrencyCode) -> float:
        """Returns the exchange rate of the given currency against the base currency."""
    def get_all_rates(self) -> dict[str, float]:
        """Returns a snapshot of all exchange rates."""
    def convert(self, amount: float, from_currency: CurrencyCode, to_currency: CurrencyCode) -> float:
        """Converts an amount from one currency to another."""
