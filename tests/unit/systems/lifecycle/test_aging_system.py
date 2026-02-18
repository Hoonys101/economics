import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.aging_system import AgingSystem, IAgingFirm
from simulation.dtos.api import SimulationState
from simulation.interfaces.market_interface import IMarket
from modules.system.api import DEFAULT_CURRENCY, ICurrencyHolder
from modules.finance.api import IFinancialEntity

class MockMarket:
    def __init__(self):
        self.id = "market"
        self.buy_orders = {}
        self.sell_orders = {}
        self.matched_transactions = []
    def get_daily_avg_price(self): return 10.0
    def get_daily_volume(self): return 100.0
    def get_price(self, item_id): return 10.0

class MockWallet:
    def __init__(self, balance):
        self.balance_pennies = balance
    def deposit(self, amount, currency="USD"): pass
    def withdraw(self, amount, currency="USD"): pass

class MockFirm:
    def __init__(self, balance=-1000, distress=False, counter=0):
        self.id = 1
        self.is_active = True
        self.age = 1
        self.needs = {"liquidity_need": 0.0}
        self.wallet = MockWallet(balance)
        self.finance_state = MagicMock()
        self.finance_state.distress_tick_counter = counter
        self.finance_state.consecutive_loss_turns = 0
        self.finance_state.is_distressed = distress
        self.config = MagicMock()
        self.finance_engine = MagicMock()
        self.finance_engine.check_bankruptcy = MagicMock()

    def get_all_items(self):
        return {"wood": 10.0}

    def get_balance(self, currency="USD"):
        return self.wallet.balance_pennies

    def get_assets_by_currency(self):
        return {"USD": self.wallet.balance_pennies}

class TestAgingSystem:
    @pytest.fixture
    def aging_system(self):
        config = MagicMock()
        config.ASSETS_CLOSURE_THRESHOLD = 0.0
        config.FIRM_CLOSURE_TURNS_THRESHOLD = 5
        config.LIQUIDITY_NEED_INCREASE_RATE = 1.0
        config.DISTRESS_GRACE_PERIOD = 5
        config.GOODS_INITIAL_PRICE = {"default": 10.0}
        config.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0

        demographic_manager = MagicMock()
        logger = MagicMock()

        return AgingSystem(config, demographic_manager, logger)

    def test_execute_delegation(self, aging_system):
        state = MagicMock()
        state.households = []
        state.firms = []

        result = aging_system.execute(state)

        aging_system.demographic_manager.process_aging.assert_called_once()
        assert isinstance(result, list) # Verify return type

    def test_firm_distress(self, aging_system):
        firm = MockFirm(balance=-1000, distress=False, counter=0)
        assert isinstance(firm, IAgingFirm)

        state = MagicMock()
        state.firms = [firm]
        state.households = []

        market = MockMarket()
        state.markets = {"wood": market}
        state.time = 1
        state.market_data = {}

        result = aging_system.execute(state)

        assert firm.finance_state.is_distressed is True
        assert firm.finance_state.distress_tick_counter == 1
        assert isinstance(result, list)

    def test_firm_grace_period_config(self, aging_system):
        aging_system.config.DISTRESS_GRACE_PERIOD = 10

        firm = MockFirm(balance=-1000, distress=True, counter=9)

        state = MagicMock()
        state.firms = [firm]
        state.households = []

        market = MockMarket()
        state.markets = {"wood": market}
        state.time = 1
        state.market_data = {}

        aging_system.execute(state)

        assert firm.finance_state.distress_tick_counter == 10
        assert firm.is_active is True
