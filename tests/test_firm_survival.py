import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.aging_system import AgingSystem, IAgingFirm
from modules.finance.api import IFinancialEntity, OMOInstructionDTO
from simulation.systems.central_bank_system import CentralBankSystem

# --- Mock Classes ---

class MockWallet(IFinancialEntity):
    def __init__(self, balance):
        self._balance = balance
        self.id = 1

    @property
    def balance_pennies(self) -> int:
        return self._balance

    def deposit(self, amount_pennies: int, currency="USD"):
        self._balance += amount_pennies

    def withdraw(self, amount_pennies: int, currency="USD"):
        self._balance -= amount_pennies

class MockFirm(IAgingFirm):
    def __init__(self, id, assets, loss_turns):
        self.id = id
        self.is_active = True
        self.age = 10
        self.needs = {"liquidity_need": 100.0}
        self.finance_state = MagicMock()
        self.finance_state.consecutive_loss_turns = loss_turns
        self.finance_state.is_distressed = False
        self.finance_state.distress_tick_counter = 0
        self.wallet = MockWallet(assets)
        self.config = MagicMock()
        self.finance_engine = MagicMock()

    def get_balance(self, currency):
        return self.wallet.balance_pennies

    def get_all_items(self):
        return {}

@pytest.fixture
def aging_system():
    config = MagicMock()
    config.ASSETS_CLOSURE_THRESHOLD = 0.0 # 0 pennies
    config.FIRM_CLOSURE_TURNS_THRESHOLD = 20
    config.LIQUIDITY_NEED_INCREASE_RATE = 0.0
    config.DISTRESS_GRACE_PERIOD = 5
    config.GOODS_INITIAL_PRICE = {"default": 10.0}

    demographic_manager = MagicMock()
    logger = MagicMock()

    return AgingSystem(config, demographic_manager, logger)

def test_solvent_firm_survival(aging_system):
    # Firm with 1M pennies (solvent) but 20 loss turns
    firm = MockFirm(id=1, assets=1_000_000, loss_turns=20)

    state = MagicMock()
    state.firms = [firm]
    state.households = []
    state.markets = {}
    state.time = 1
    state.market_data = {}

    aging_system._process_firm_lifecycle(state)

    # Assert firm is still active (Solvency Bypass)
    assert firm.is_active is True, "Solvent firm should survive even with max loss turns"

def test_insolvent_firm_death(aging_system):
    # Firm with 0 pennies (insolvent) and 0 loss turns
    firm = MockFirm(id=2, assets=0, loss_turns=0)

    state = MagicMock()
    state.firms = [firm]
    state.households = []
    state.markets = {}
    state.time = 1
    state.market_data = {}

    aging_system._process_firm_lifecycle(state)

    assert firm.is_active is False, "Insolvent firm should die"

def test_zombie_firm_death(aging_system):
    # Firm with negative assets (insolvent) and 20 loss turns
    firm = MockFirm(id=3, assets=-100, loss_turns=20)

    state = MagicMock()
    state.firms = [firm]
    state.households = []
    state.markets = {}
    state.time = 1
    state.market_data = {}

    aging_system._process_firm_lifecycle(state)

    assert firm.is_active is False, "Zombie firm should die"

def test_omo_quantity_calculation():
    # Setup Central Bank System
    cb_agent = MagicMock()
    cb_agent.id = -2
    settlement = MagicMock()
    transactions = []

    cb_system = CentralBankSystem(cb_agent, settlement, transactions)

    # Instruction: Buy 1M pennies worth of bonds
    instruction = OMOInstructionDTO(operation_type="purchase", target_amount=1_000_000)

    # Note: Existing code might crash due to dict access on DTO.
    # If it crashes, that's a failure we need to fix.
    try:
        orders = cb_system.execute_open_market_operation(instruction)
    except TypeError:
        pytest.fail("execute_open_market_operation failed to access DTO attributes (likely using dict access)")

    assert len(orders) == 1
    order = orders[0]

    # Check Quantity
    # Expected: 1,000,000 // 10000 (Price) = 100
    # Currently bugged code produces 1,000,000

    assert order.quantity < 1_000_000, f"Quantity {order.quantity} is too high (Hyperinflation)"
    assert order.quantity > 0, "Quantity should be positive"
