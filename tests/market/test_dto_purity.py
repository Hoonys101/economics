import pytest
import uuid
from unittest.mock import MagicMock
from pydantic import ValidationError
from modules.market.api import CanonicalOrderDTO, OrderTelemetrySchema, MarketSide

# Check if Pydantic is mocked (ValidationError is a Mock object)
IS_PYDANTIC_MOCKED = isinstance(ValidationError, MagicMock) or (hasattr(ValidationError, '__class__') and 'Mock' in ValidationError.__class__.__name__)

def test_canonical_order_dto_instantiation():
    """Test that CanonicalOrderDTO can be instantiated with required fields."""
    order = CanonicalOrderDTO(
        agent_id=1,
        side="BUY",
        item_id="stock_101",
        quantity=10.0,
        price_pennies=1050,
        market_id="stock_market"
    )
    assert order.price_pennies == 1050
    assert order.price == 10.50
    assert order.price_limit == 0.0 # Default
    assert order.side == "BUY"
    assert order.order_type == "BUY"

@pytest.mark.skipif(IS_PYDANTIC_MOCKED, reason="Pydantic is mocked")
def test_order_telemetry_schema_serialization():
    """Test that OrderTelemetrySchema serializes correctly."""
    order = CanonicalOrderDTO(
        agent_id=1,
        side="BUY",
        item_id="stock_101",
        quantity=10.0,
        price_pennies=1050,
        market_id="stock_market"
    )

    schema = OrderTelemetrySchema.from_canonical(order, timestamp=100)
    assert schema.agent_id == 1
    assert schema.side == MarketSide.BUY
    assert schema.item_id == "stock_101"
    assert schema.quantity == 10.0
    assert schema.price_pennies == 1050
    assert schema.price_display == 10.50
    assert schema.market_id == "stock_market"
    assert schema.timestamp == 100

    # Check JSON dump
    data = schema.model_dump()
    assert data["price_pennies"] == 1050
    assert data["price_display"] == 10.50
    assert data["side"] == "BUY"

@pytest.mark.skipif(IS_PYDANTIC_MOCKED, reason="Pydantic is mocked")
def test_order_telemetry_schema_validation():
    """Test that invalid side raises ValidationError."""
    with pytest.raises(ValidationError):
        OrderTelemetrySchema(
            id=str(uuid.uuid4()),
            agent_id=1,
            side="HOLD", # Invalid side
            item_id="stock_101",
            quantity=10.0,
            price_pennies=1050,
            price_display=10.50,
            market_id="stock_market"
        )

def test_canonical_order_legacy_fields():
    """Test that legacy fields work as expected."""
    order = CanonicalOrderDTO(
        agent_id=1,
        side="SELL",
        item_id="stock_102",
        quantity=5.0,
        price_pennies=2000,
        market_id="stock_market",
        price_limit=25.00 # Explicit legacy value
    )
    # If price_limit is set, .price returns it
    assert order.price == 25.00
    assert order.price_pennies == 2000 # SSoT remains distinct

    order2 = CanonicalOrderDTO(
        agent_id=1,
        side="SELL",
        item_id="stock_102",
        quantity=5.0,
        price_pennies=2000,
        market_id="stock_market"
        # price_limit default 0.0
    )
    # If price_limit is 0.0, .price returns pennies/100
    assert order2.price == 20.00
