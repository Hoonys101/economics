import pytest
from modules.market.api import StockIDHelper


class TestStockIDHelper:

    def test_stock_id_helper_valid(self):
        assert StockIDHelper.is_valid_stock_id('stock_101') is True
        assert StockIDHelper.parse_firm_id('stock_101') == 101
        assert StockIDHelper.format_stock_id(101) == 'stock_101'

    def test_stock_id_helper_invalid(self):
        assert StockIDHelper.is_valid_stock_id('bond_101') is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id('bond_101')
        assert StockIDHelper.is_valid_stock_id('stock101') is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id('stock101')
        assert StockIDHelper.is_valid_stock_id('stock_abc') is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id('stock_abc')
        assert StockIDHelper.is_valid_stock_id('101') is False
        with pytest.raises(ValueError):
            StockIDHelper.parse_firm_id('101')

    def test_format_stock_id_handles_string(self):
        assert StockIDHelper.format_stock_id('101') == 'stock_101'
