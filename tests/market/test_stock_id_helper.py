import pytest
from modules.market.api import StockIDHelper

class TestStockIDHelper:
    def test_stock_id_helper_valid(self):
        assert StockIDHelper.is_valid_stock_id("stock_101") is True
        assert StockIDHelper.parse_firm_id("stock_101") == 101
        assert StockIDHelper.format_stock_id(101) == "stock_101"

    def test_stock_id_helper_invalid(self):
        # Invalid prefix
        assert StockIDHelper.is_valid_stock_id("bond_101") is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id("bond_101")

        # Invalid format (no separator)
        assert StockIDHelper.is_valid_stock_id("stock101") is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id("stock101")

        # Invalid ID part (not digit)
        assert StockIDHelper.is_valid_stock_id("stock_abc") is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id("stock_abc")

        # Legacy format (just ID) - strict mode fails
        assert StockIDHelper.is_valid_stock_id("101") is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id("101")

    def test_format_stock_id_handles_string(self):
        assert StockIDHelper.format_stock_id("101") == "stock_101"
