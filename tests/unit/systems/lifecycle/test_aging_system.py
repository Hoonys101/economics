import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.aging_system import AgingSystem
from simulation.systems.lifecycle.api import IAgingFirm, IFinanceEngine
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
    def place_order(self, order, tick): pass

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
        # Ensure finance_engine satisfies IFinanceEngine protocol
        self.finance_engine = MagicMock(spec=IFinanceEngine)
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
        config.ASSETS_CLOSURE_THRESHOLD = 0.0 # Pennies will be 0
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

    def test_solvency_gate_active(self, aging_system):
        """
        Verify a firm with high assets but high loss turns is NOT closed (Solvency Gate).
        """
        # Threshold is 0.0 (0 pennies). Let's set it to 100.0 (10000 pennies)
        aging_system.config.ASSETS_CLOSURE_THRESHOLD = 100.0
        threshold_pennies = 10000

        # Solvent if > 2 * threshold = 20000 pennies
        firm = MockFirm(balance=25000) # 250.00
        firm.finance_state.consecutive_loss_turns = 10 # > 5 threshold
        firm.finance_state.distress_tick_counter = 0 # Not in distress grace period loop
        firm.finance_state.is_distressed = False

        state = MagicMock()
        state.firms = [firm]
        state.households = []
        state.markets = {}
        state.time = 1
        state.market_data = {}

        aging_system.execute(state)

        assert firm.is_active is True # Should survive due to Solvency Gate

    def test_solvency_gate_inactive(self, aging_system):
        """
        Verify a firm with low assets AND high loss turns IS closed.
        """
        aging_system.config.ASSETS_CLOSURE_THRESHOLD = 100.0
        threshold_pennies = 10000

        # Not solvent if <= 2 * threshold = 20000 pennies
        firm = MockFirm(balance=15000) # 150.00 (Between 1x and 2x threshold, technically solvent by strict def? No, strict is > 2x)
        # Wait, Solvency Gate says: is_solvent = current_assets > (threshold * 2)
        # If assets = 15000, threshold = 10000. 15000 < 20000. So NOT solvent.
        # If loss turns high, it should close.

        firm.finance_state.consecutive_loss_turns = 10 # > 5 threshold
        firm.finance_state.distress_tick_counter = 100 # Grace period expired
        firm.finance_state.is_distressed = True

        state = MagicMock()
        state.firms = [firm]
        state.households = []
        state.markets = {}
        state.time = 1
        state.market_data = {}

        aging_system.execute(state)

        assert firm.is_active is False # Should close
