import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.components.finance_department import FinanceDepartment
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.dtos.api import SimulationState
from simulation.models import Order
from modules.market.api import OrderDTO
from tests.utils.factories import create_firm_config_dto, create_household_config_dto

class TestGraceProtocol:

    @pytest.fixture
    def setup_firm_state(self):
        config = create_firm_config_dto()
        config.ASSETS_CLOSURE_THRESHOLD = 0.0
        config.FIRM_CLOSURE_TURNS_THRESHOLD = 5
        config.LIQUIDITY_NEED_INCREASE_RATE = 1.0

        # Use MagicMock without spec to avoid property/attribute conflicts with real FinanceDepartment attachment
        firm = MagicMock()
        firm.id = 1
        firm.is_active = True
        firm.age = 10
        firm.needs = {"liquidity_need": 0.0}
        # firm.finance will be overwritten below, but we initialize common attrs
        firm.inventory = {"wood": 10.0}
        firm.last_prices = {"wood": 10.0}
        firm.get_financial_snapshot.return_value = {} # Mock helper if needed

        # Real FinanceDepartment to test logic
        # FinanceDepartment expects a firm object, our mock is sufficient if it behaves like one
        firm.finance = FinanceDepartment(firm, config, initial_capital=0.0)
        # Mock logger
        firm.logger = MagicMock()

        return firm, config

    def test_firm_grace_protocol(self, setup_firm_state):
        firm, config = setup_firm_state

        # Setup Markets
        market_mock = MagicMock()
        markets = {"wood": market_mock}

        state = MagicMock(spec=SimulationState)
        state.firms = [firm]
        state.markets = markets
        state.time = 1

        # Lifecycle Manager
        manager = AgentLifecycleManager(config, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())

        # Run 1: Enter Distress
        firm.finance._cash = -10.0 # Cash Crunch
        manager._process_firm_lifecycle(state)

        assert firm.finance.is_distressed is True
        assert firm.finance.distress_tick_counter == 1
        assert firm.is_active is True # Saved

        # Check Order Placement
        # manager._process_firm_lifecycle calls market.place_order(order, time)
        assert market_mock.place_order.called
        call_args = market_mock.place_order.call_args
        order = call_args[0][0]
        # Order is OrderDTO
        assert isinstance(order, OrderDTO)
        assert order.side == "SELL"
        assert order.item_id == "wood"
        assert order.price_limit == 8.0 # 10.0 * 0.8

        # Run 2-5: Stay in Distress
        for i in range(2, 6):
            state.time = i
            manager._process_firm_lifecycle(state)
            assert firm.finance.distress_tick_counter == i
            assert firm.is_active is True

        # Run 6: Death
        state.time = 6
        manager._process_firm_lifecycle(state)
        assert firm.finance.distress_tick_counter == 6
        # Should fall through to closure check
        # Since assets <= threshold (0 <= 0), it should close.
        # But wait, logic says:
        # if distress_tick_counter > 5: pass (allow closure)
        # then if assets <= threshold: active=False
        assert firm.is_active is False

    @pytest.fixture
    def setup_household_state(self):
        config = create_household_config_dto()
        config.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0

        hh = MagicMock(spec=Household)
        hh.id = 101
        hh.is_active = True
        hh.needs = {"survival": 95.0} # Critical (> 90)
        hh.inventory = {}
        hh.shares_owned = {1: 10.0} # Has stocks
        hh.distress_tick_counter = 0
        hh.logger = MagicMock()

        # We need the real trigger_emergency_liquidation logic?
        # But Household is mocked. We should assign the real method or mock the return.
        # Ideally we use real Household but it has many dependencies.
        # Let's bind the method if possible or just implement the method on the mock
        # or use real Household with mocked components.

        # Let's try real Household with mocked dependencies
        real_hh = Household(
            id=101,
            talent=MagicMock(),
            goods_data=[{"id": "wood", "initial_price": 10.0}],
            initial_assets=0.0,
            initial_needs={"survival": 95.0},
            decision_engine=MagicMock(),
            value_orientation="traditional",
            personality=MagicMock(),
            config_dto=config,
            logger=MagicMock()
        )
        # Update portfolio correctly
        real_hh._econ_state.portfolio.add(firm_id=1, quantity=10.0, price=10.0)

        return real_hh, config

    def test_household_grace_protocol(self, setup_household_state):
        hh, config = setup_household_state

        # Setup Markets
        stock_market_mock = MagicMock()
        state = MagicMock(spec=SimulationState)
        state.households = [hh]
        state.markets = {}
        state.stock_market = stock_market_mock
        state.time = 1

        manager = AgentLifecycleManager(config, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())

        # Run 1: Enter Distress
        manager._process_household_lifecycle(state)

        assert hh.distress_tick_counter == 1

        # Check Stock Order
        assert stock_market_mock.place_order.called
        order = stock_market_mock.place_order.call_args[0][0]
        # Should now be OrderDTO
        assert isinstance(order, OrderDTO)
        assert order.item_id == "stock_1"

        # Test Death Override in update_needs
        # Mock social component to return False (Death)
        hh.social_component = MagicMock()
        hh.social_component.update_psychology.return_value = (MagicMock(), {"survival": 100}, [], False) # is_active=False

        hh.update_needs(current_tick=1)

        # Should be saved by Grace Protocol
        assert hh.is_active is True
        hh.logger.info.assert_called()
