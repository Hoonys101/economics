import unittest
from unittest.mock import MagicMock
from modules.finance.exchange.engine import CurrencyExchangeEngine
from modules.system.api import DEFAULT_CURRENCY

class TestCurrencyExchangeEngine(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.get.side_effect = self.mock_get_config

    def mock_get_config(self, key, default=None):
        if key == "simulation.currency_exchange.parity":
            return {
                "USD": 1.0,
                "KRW": 1300.0,
                "EUR": 0.92
            }
        return default

    def test_load_parity(self):
        engine = CurrencyExchangeEngine(self.mock_config)
        rate = engine.get_exchange_rate("KRW")
        self.assertEqual(rate, 1300.0)
        self.assertEqual(engine.get_exchange_rate("USD"), 1.0)
        self.assertEqual(engine.get_exchange_rate("EUR"), 0.92)

    def test_convert(self):
        engine = CurrencyExchangeEngine(self.mock_config)

        # USD to KRW
        # 1 USD -> 1300 KRW
        converted = engine.convert(10.0, "USD", "KRW")
        self.assertEqual(converted, 13000.0)

        # KRW to USD
        # 1300 KRW -> 1 USD
        converted = engine.convert(1300.0, "KRW", "USD")
        self.assertAlmostEqual(converted, 1.0)

        # KRW to EUR
        # 1300 KRW -> 1 USD -> 0.92 EUR
        converted = engine.convert(1300.0, "KRW", "EUR")
        self.assertAlmostEqual(converted, 0.92)

    def test_missing_config(self):
        empty_config = MagicMock()
        empty_config.get.return_value = {}

        engine = CurrencyExchangeEngine(empty_config)
        rate = engine.get_exchange_rate("USD")
        self.assertEqual(rate, 1.0) # Should default to 1.0

        # Unknown currency should default to 1.0 based on current implementation
        # (Though we might want to change this later, currently it defaults to 1.0 in get() method)
        rate_unknown = engine.get_exchange_rate("ZZZ")
        self.assertEqual(rate_unknown, 1.0)

if __name__ == '__main__':
    unittest.main()
