import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.components.state.firm_state_models import FinanceState
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.systems.lifecycle.aging_system import IAgingFirm
from simulation.interfaces.market_interface import IMarket
from simulation.dtos.api import SimulationState
from simulation.models import Order, Transaction
from modules.market.api import OrderDTO
from tests.utils.factories import create_firm_config_dto, create_household_config_dto
from modules.system.api import ICurrencyHolder, DEFAULT_CURRENCY
from typing import Dict, List

# Concrete Mock Class for Firm
class DummyFirm(IAgingFirm, ICurrencyHolder):
    def __init__(self, config):
        self.id = 1
        self.is_active = True
        self.age = 10
        self.needs = {'liquidity_need': 0.0}
        self.inventory = {'wood': 10.0}
        self.last_prices = {'wood': 10.0}
        self.finance_state = FinanceState()
        self.finance_engine = MagicMock()
        self.wallet = MagicMock()
        self.wallet.get_balance.return_value = 0
        self.config = config
        self.logger = MagicMock()
        self._balance = 0 # Pennies

    def get_all_items(self):
        return self.inventory

    def get_balance(self, currency):
        return self._balance

    def get_assets_by_currency(self):
        return {DEFAULT_CURRENCY: self._balance}

    def deposit(self, amount, currency):
        pass

    def withdraw(self, amount, currency):
        pass

# Concrete Mock Class for Market
class DummyMarket(IMarket):
    def __init__(self):
        self.id = "wood"
        self._buy_orders: Dict[str, List[Order]] = {}
        self._sell_orders: Dict[str, List[Order]] = {}
        self._matched_transactions = []
        self.avg_price = 10.0 # Used by tests

    @property
    def buy_orders(self) -> Dict[str, List[Order]]:
        return self._buy_orders

    @property
    def sell_orders(self) -> Dict[str, List[Order]]:
        return self._sell_orders

    @property
    def matched_transactions(self) -> List[Transaction]:
        return self._matched_transactions

    def get_daily_avg_price(self) -> float:
        return self.avg_price

    def get_daily_volume(self) -> float:
        return 0.0

    def get_price(self, item_id: str) -> float:
        return self.avg_price

class TestGraceProtocol:

    @pytest.fixture
    def setup_firm_state(self):
        config = create_firm_config_dto()
        config.ASSETS_CLOSURE_THRESHOLD = 0.0
        config.FIRM_CLOSURE_TURNS_THRESHOLD = 5
        config.LIQUIDITY_NEED_INCREASE_RATE = 1.0

        firm = DummyFirm(config)

        return (firm, config)

    def test_firm_grace_protocol(self, setup_firm_state):
        firm, config = setup_firm_state
        market = DummyMarket()

        markets = {'wood': market}
        state = MagicMock(spec=SimulationState)
        state.firms = [firm]
        state.markets = markets
        state.time = 1
        manager = AgentLifecycleManager(
            config_module=config,
            demographic_manager=MagicMock(),
            inheritance_manager=MagicMock(),
            firm_system=MagicMock(),
            settlement_system=MagicMock(),
            public_manager=MagicMock(),
            logger=MagicMock(),
            household_factory=MagicMock()
        )

        # firm.wallet.get_balance.return_value = -10.0 # This was for MagicMock
        # Update dummy firm balance
        firm._balance = -1000 # Pennies (-10.0)

        manager.aging_system._process_firm_lifecycle(state)
        assert firm.finance_state.is_distressed is True
        assert firm.finance_state.distress_tick_counter == 1
        assert firm.is_active is True
        for i in range(2, 6):
            state.time = i
            manager.aging_system._process_firm_lifecycle(state)
            assert firm.finance_state.distress_tick_counter == i
            assert firm.is_active is True
        state.time = 6
        manager.aging_system._process_firm_lifecycle(state)
        assert firm.finance_state.distress_tick_counter == 6
        assert firm.is_active is False

    @pytest.fixture
    def setup_household_state(self):
        config = create_household_config_dto()
        config.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
        hh = MagicMock(spec=Household)
        hh.id = 101
        hh.is_active = True
        hh.needs = {'survival': 95.0}
        hh.inventory = {}
        hh.shares_owned = {1: 10.0}
        hh.distress_tick_counter = 0
        hh.logger = MagicMock()
        hh._bio_state = MagicMock()
        hh._bio_state.is_active = True
        hh._bio_state.needs = {'survival': 95.0}
        hh._econ_state = MagicMock()
        hh._econ_state.inventory = {}
        hh._econ_state.portfolio.to_legacy_dict.return_value = {1: 10.0}
        hh.trigger_emergency_liquidation.return_value = [OrderDTO(agent_id=101, side='SELL', item_id='stock_1', quantity=10.0, price_pennies=int(0.0 * 100), price_limit=0.0, market_id='stock_market')]
        hh.update_needs = MagicMock()
        return (hh, config)

    def test_household_grace_protocol(self, setup_household_state):
        hh, config = setup_household_state
        stock_market_mock = MagicMock()
        state = MagicMock(spec=SimulationState)
        state.households = [hh]
        state.markets = {}
        state.stock_market = stock_market_mock
        state.time = 1
        manager = AgentLifecycleManager(
            config_module=config,
            demographic_manager=MagicMock(),
            inheritance_manager=MagicMock(),
            firm_system=MagicMock(),
            settlement_system=MagicMock(),
            public_manager=MagicMock(),
            logger=MagicMock(),
            household_factory=MagicMock()
        )
        manager.aging_system._process_household_lifecycle(state)
        assert hh.distress_tick_counter == 1
        assert stock_market_mock.place_order.called
        order = stock_market_mock.place_order.call_args[0][0]
        assert isinstance(order, OrderDTO)
        assert order.item_id == 'stock_1'
