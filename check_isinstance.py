from simulation.markets.stock_market import StockMarket
from simulation.interfaces.market_interface import IMarket
from unittest.mock import MagicMock

def test_isinstance():
    m = StockMarket(MagicMock(), MagicMock())
    print(f"Is instance: {isinstance(m, IMarket)}")

if __name__ == "__main__":
    test_isinstance()
