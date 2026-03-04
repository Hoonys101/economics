import pytest
from unittest.mock import MagicMock
from modules.market.api import CanonicalOrderDTO, IPriceLimitEnforcer, IIndexCircuitBreaker
from modules.market.safety_dtos import PriceLimitConfigDTO, ValidationResultDTO
from modules.market.safety.price_limit import PriceLimitEnforcer
from simulation.markets.order_book_market import OrderBookMarket


class TestPriceLimitEnforcer:

    def test_disabled_allows_all(self):
        config = PriceLimitConfigDTO(id='test', is_enabled=False, mode=
            'STATIC', static_ceiling=100)
        enforcer = PriceLimitEnforcer(config)
        order = CanonicalOrderDTO(agent_id=1, side='BUY', item_id='apple',
            quantity=1, price_pennies=9999, market_id='m')
        result = enforcer.validate_order(order)
        assert result.is_valid

    def test_static_limits(self):
        config = PriceLimitConfigDTO(id='test', is_enabled=True, mode=
            'STATIC', static_ceiling=200, static_floor=100)
        enforcer = PriceLimitEnforcer(config)
        assert enforcer.validate_order(CanonicalOrderDTO(agent_id=1, side=
            'BUY', item_id='a', quantity=1, price_pennies=150, market_id='m')
            ).is_valid
        res_high = enforcer.validate_order(CanonicalOrderDTO(agent_id=1,
            side='BUY', item_id='a', quantity=1, price_pennies=201,
            market_id='m'))
        assert not res_high.is_valid
        assert 'exceeds static ceiling' in res_high.reason
        res_low = enforcer.validate_order(CanonicalOrderDTO(agent_id=1,
            side='BUY', item_id='a', quantity=1, price_pennies=99,
            market_id='m'))
        assert not res_low.is_valid
        assert 'below static floor' in res_low.reason

    def test_dynamic_limits(self):
        config = PriceLimitConfigDTO(id='test', is_enabled=True, mode=
            'DYNAMIC', base_limit=0.1)
        enforcer = PriceLimitEnforcer(config)
        enforcer.set_reference_price(1000)
        assert enforcer.validate_order(CanonicalOrderDTO(agent_id=1, side=
            'BUY', item_id='a', quantity=1, price_pennies=1000, market_id='m')
            ).is_valid
        assert enforcer.validate_order(CanonicalOrderDTO(agent_id=1, side=
            'BUY', item_id='a', quantity=1, price_pennies=1100, market_id='m')
            ).is_valid
        assert enforcer.validate_order(CanonicalOrderDTO(agent_id=1, side=
            'BUY', item_id='a', quantity=1, price_pennies=900, market_id='m')
            ).is_valid
        assert not enforcer.validate_order(CanonicalOrderDTO(agent_id=1,
            side='BUY', item_id='a', quantity=1, price_pennies=1101,
            market_id='m')).is_valid
        assert not enforcer.validate_order(CanonicalOrderDTO(agent_id=1,
            side='BUY', item_id='a', quantity=1, price_pennies=899,
            market_id='m')).is_valid

    def test_dynamic_discovery_phase(self):
        config = PriceLimitConfigDTO(id='test', is_enabled=True, mode=
            'DYNAMIC', base_limit=0.1)
        enforcer = PriceLimitEnforcer(config)
        assert enforcer.validate_order(CanonicalOrderDTO(agent_id=1, side=
            'BUY', item_id='a', quantity=1, price_pennies=99999, market_id='m')
            ).is_valid


class TestOrderBookMarketSafetyIntegration:

    def test_market_rejects_invalid_order(self):
        mock_enforcer = MagicMock(spec=IPriceLimitEnforcer)
        mock_enforcer.validate_order.return_value = ValidationResultDTO(
            is_valid=False, reason='Mock Reject')
        market = OrderBookMarket('test_market', enforcer=mock_enforcer)
        order = CanonicalOrderDTO(agent_id=1, side='BUY', item_id='a',
            quantity=1, price_pennies=100, market_id='test_market')
        market.place_order(order, current_time=1)
        assert len(market.buy_orders.get('a', [])) == 0
        mock_enforcer.validate_order.assert_called_once()

    def test_market_accepts_valid_order(self):
        mock_enforcer = MagicMock(spec=IPriceLimitEnforcer)
        mock_enforcer.validate_order.return_value = ValidationResultDTO(
            is_valid=True)
        market = OrderBookMarket('test_market', enforcer=mock_enforcer)
        order = CanonicalOrderDTO(agent_id=1, side='BUY', item_id='a',
            quantity=1, price_pennies=100, market_id='test_market')
        market.place_order(order, current_time=1)
        assert len(market.buy_orders.get('a', [])) == 1

    def test_market_halt_blocks_order(self):
        mock_cb = MagicMock(spec=IIndexCircuitBreaker)
        mock_cb.is_active.return_value = True
        market = OrderBookMarket('test_market', circuit_breaker=mock_cb)
        order = CanonicalOrderDTO(agent_id=1, side='BUY', item_id='a',
            quantity=1, price_pennies=100, market_id='test_market')
        market.place_order(order, current_time=1)
        assert len(market.buy_orders.get('a', [])) == 0
        mock_cb.is_active.assert_called_once()
