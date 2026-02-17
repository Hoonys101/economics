import pytest
from dataclasses import dataclass
from modules.market.api import CanonicalOrderDTO, convert_legacy_order_to_canonical
from simulation.models import StockOrder

class TestMarketAdapter:
    def test_pass_through(self):
        dto = CanonicalOrderDTO(
            agent_id=1,
            side="BUY",
            item_id="stock_100",
            quantity=10.0,
            price_limit=50.0,
            price_pennies=5000,
            market_id="stock_market"
        )
        converted = convert_legacy_order_to_canonical(dto)
        assert converted is dto

    def test_convert_stock_order(self):
        legacy = StockOrder(
            agent_id=1,
            order_type="SELL",
            firm_id=100,
            quantity=5.0,
            price=45.0 # StockOrder treats this as raw value (pennies usually if int)
        )
        converted = convert_legacy_order_to_canonical(legacy)

        assert isinstance(converted, CanonicalOrderDTO)
        assert converted.agent_id == 1
        assert converted.side == "SELL"
        assert converted.item_id == "stock_100"
        assert converted.quantity == 5.0
        assert converted.price_limit == 45.0
        # StockOrder conversion logic uses int(order.price) directly
        assert converted.price_pennies == 4500
        assert converted.market_id == "stock_market"

    def test_convert_dict_legacy_format(self):
        legacy_dict = {
            "agent_id": 2,
            "order_type": "BUY",
            "firm_id": 200,
            "quantity": 20.0,
            "price": 60.0,
            "market_id": "stock_market"
        }
        converted = convert_legacy_order_to_canonical(legacy_dict)

        assert isinstance(converted, CanonicalOrderDTO)
        assert converted.agent_id == 2
        assert converted.side == "BUY"
        assert converted.item_id == "stock_200"
        assert converted.quantity == 20.0
        assert converted.price_limit == 60.0
        # Dict conversion logic: float -> dollars -> * 100
        assert converted.price_pennies == 6000

    def test_convert_dict_canonical_format(self):
        canonical_dict = {
            "agent_id": 3,
            "side": "SELL",
            "item_id": "stock_300",
            "quantity": 15.0,
            "price_limit": 55.0,
            "market_id": "stock_market"
        }
        converted = convert_legacy_order_to_canonical(canonical_dict)

        assert isinstance(converted, CanonicalOrderDTO)
        assert converted.agent_id == 3
        assert converted.side == "SELL"
        assert converted.item_id == "stock_300"
        assert converted.price_limit == 55.0
        # Dict logic again
        assert converted.price_pennies == 5500

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            convert_legacy_order_to_canonical("invalid_string")
