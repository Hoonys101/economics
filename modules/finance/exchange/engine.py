from typing import Dict, Any, Optional
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
import logging

logger = logging.getLogger(__name__)

class CurrencyExchangeEngine:
    """
    Handles currency exchange rate retrieval and conversion.
    Reads parity configuration from config/simulation.yaml.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self._parity_cache: Optional[Dict[str, float]] = None

    def _load_parity(self) -> Dict[str, float]:
        if self._parity_cache is None:
            # Safely retrieve the parity dictionary from config
            # Expecting config.simulation.currency_exchange.parity
            try:
                raw_parity = {}
                if hasattr(self.config_module, 'get'):
                     raw_parity = self.config_module.get("simulation.currency_exchange.parity", {})

                self._parity_cache = {k.upper(): float(v) for k, v in raw_parity.items()}

                # Ensure DEFAULT_CURRENCY is always 1.0
                if DEFAULT_CURRENCY not in self._parity_cache:
                    self._parity_cache[DEFAULT_CURRENCY] = 1.0

            except Exception as e:
                logger.error(f"Failed to load currency parity: {e}")
                self._parity_cache = {DEFAULT_CURRENCY: 1.0}

        return self._parity_cache

    def get_exchange_rate(self, currency: CurrencyCode) -> float:
        """Returns the exchange rate of the given currency against the base currency."""
        parities = self._load_parity()
        return parities.get(currency.upper(), 1.0)

    def get_all_rates(self) -> Dict[str, float]:
        """Returns a snapshot of all exchange rates."""
        return self._load_parity().copy()

    def convert(self, amount: float, from_currency: CurrencyCode, to_currency: CurrencyCode) -> float:
        """Converts an amount from one currency to another."""
        if from_currency == to_currency:
            return amount

        from_rate = self.get_exchange_rate(from_currency)
        to_rate = self.get_exchange_rate(to_currency)

        # Avoid division by zero
        if from_rate == 0:
            logger.error(f"Exchange rate for {from_currency} is 0. Returning 0.")
            return 0.0

        return (amount / from_rate) * to_rate
