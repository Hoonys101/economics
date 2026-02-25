import pytest
from unittest.mock import MagicMock
from simulation.markets.circuit_breaker import PriceLimitEnforcer
from modules.market.safety_dtos import PriceLimitConfigDTO, ValidationResultDTO
from modules.market.api import CanonicalOrderDTO
from modules.finance.api import FloatIncursionError

class TestPriceLimitEnforcer:
    @pytest.fixture
    def dynamic_config(self):
        return PriceLimitConfigDTO(
            id="test_dynamic",
            is_enabled=True,
            mode="DYNAMIC",
            base_limit=0.15
        )

    @pytest.fixture
    def static_config(self):
        return PriceLimitConfigDTO(
            id="test_static",
            is_enabled=True,
            mode="STATIC",
            static_floor=500,
            static_ceiling=2000
        )

    def test_float_reference_price_raises_error(self, dynamic_config):
        enforcer = PriceLimitEnforcer(config=dynamic_config)
        with pytest.raises(FloatIncursionError):
            enforcer.set_reference_price(10.5)

    def test_float_order_price_raises_error(self, dynamic_config):
        enforcer = PriceLimitEnforcer(config=dynamic_config)
        enforcer.set_reference_price(1000)

        # CanonicalOrderDTO with float price_pennies (mocked or forced)
        # CanonicalOrderDTO normally enforces types but we can force it or mock it
        order = MagicMock(spec=CanonicalOrderDTO)
        order.price_pennies = 10.5

        with pytest.raises(FloatIncursionError):
            enforcer.validate_order(order)

    def test_dynamic_mode_accuracy(self, dynamic_config):
        enforcer = PriceLimitEnforcer(config=dynamic_config)
        enforcer.set_reference_price(1000)

        # Limit margin = 1000 * 0.15 = 150
        # Lower = 1000 - 150 = 850
        # Upper = 1000 + 150 = 1150

        # Valid order
        order_valid = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=1000, market_id="mkt", price_limit=10.0
        )
        result = enforcer.validate_order(order_valid)
        assert result.is_valid is True

        # Below floor
        order_low = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=849, market_id="mkt", price_limit=8.49
        )
        result = enforcer.validate_order(order_low)
        assert result.is_valid is False
        assert result.reason == "PRICE_BELOW_DYNAMIC_FLOOR"
        assert result.adjusted_price == 850

        # Above ceiling
        order_high = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=1151, market_id="mkt", price_limit=11.51
        )
        result = enforcer.validate_order(order_high)
        assert result.is_valid is False
        assert result.reason == "PRICE_ABOVE_DYNAMIC_CEILING"
        assert result.adjusted_price == 1150

    def test_discovery_mode(self, dynamic_config):
        enforcer = PriceLimitEnforcer(config=dynamic_config)
        enforcer.set_reference_price(0) # Discovery mode

        order = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=999999, market_id="mkt", price_limit=9999.99
        )
        result = enforcer.validate_order(order)
        assert result.is_valid is True

    def test_static_mode_accuracy(self, static_config):
        enforcer = PriceLimitEnforcer(config=static_config)
        # Reference price ignored in static mode

        # Valid order (1000 is between 500 and 2000)
        order_valid = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=1000, market_id="mkt", price_limit=10.0
        )
        result = enforcer.validate_order(order_valid)
        assert result.is_valid is True

        # Below floor (499 < 500)
        order_low = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=499, market_id="mkt", price_limit=4.99
        )
        result = enforcer.validate_order(order_low)
        assert result.is_valid is False
        assert result.reason == "PRICE_BELOW_STATIC_FLOOR"
        assert result.adjusted_price == 500

        # Above ceiling (2001 > 2000)
        order_high = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=1.0,
            price_pennies=2001, market_id="mkt", price_limit=20.01
        )
        result = enforcer.validate_order(order_high)
        assert result.is_valid is False
        assert result.reason == "PRICE_ABOVE_STATIC_CEILING"
        assert result.adjusted_price == 2000
