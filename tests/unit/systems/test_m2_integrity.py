import pytest
from unittest.mock import MagicMock, ANY
from simulation.systems.settlement_system import SettlementSystem
from simulation.systems.transaction_processor import TransactionProcessor
from modules.finance.api import IFinancialAgent, IBank, IMonetaryLedger, ITransaction
from modules.system.constants import ID_CENTRAL_BANK, ID_GOVERNMENT, ID_BANK
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction
from simulation.dtos.api import SimulationState

# Reuse MockAgent from existing tests or create a simple one
class MockAgent(IFinancialAgent):
    def __init__(self, agent_id, assets=0):
        self._id = agent_id
        self._assets = int(assets)
        self.is_active = True

    @property
    def id(self):
        return self._id

    @property
    def balance_pennies(self) -> int:
        return self._assets

    def get_balance(self, currency=DEFAULT_CURRENCY) -> int:
        if currency == DEFAULT_CURRENCY:
            return self._assets
        return 0

    def _withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self._assets -= int(amount)

    def _deposit(self, amount, currency=DEFAULT_CURRENCY):
        self._assets += int(amount)

    def withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self._withdraw(amount, currency)

    def deposit(self, amount, currency=DEFAULT_CURRENCY):
        self._deposit(amount, currency)

    def get_assets_by_currency(self):
        return {DEFAULT_CURRENCY: self._assets}

class MockBank(MockAgent, IBank):
    def __init__(self, agent_id=ID_BANK, assets=1000000):
        super().__init__(agent_id, assets)
        self.accounts = {}

    def get_customer_balance(self, agent_id): return 0
    def get_debt_status(self, borrower_id): return None
    def terminate_loan(self, loan_id): return None
    def withdraw_for_customer(self, agent_id, amount): return False
    def get_total_deposits(self): return 0
    def close_account(self, agent_id): return 0
    def repay_loan(self, loan_id, amount): return amount
    def receive_repayment(self, borrower_id, amount): return amount
    def grant_loan(self, *args, **kwargs): return None
    def stage_loan(self, *args, **kwargs): return None
    def get_interest_rate(self): return 0.05

@pytest.fixture
def mock_ledger():
    return MagicMock(spec=IMonetaryLedger)

@pytest.fixture
def settlement_system(mock_ledger):
    bank = MockBank()
    registry = MagicMock()
    # Mock registry behavior
    registry.get_agent.side_effect = lambda uid: bank if uid == ID_BANK else None

    system = SettlementSystem(bank=bank, agent_registry=registry)
    system.set_monetary_ledger(mock_ledger)
    return system

def test_transfer_m2_to_m2_no_expansion(settlement_system, mock_ledger):
    """
    Household -> Household (M2 -> M2)
    Should NOT trigger expansion or contraction.
    """
    sender = MockAgent(101, 1000) # Household
    receiver = MockAgent(102, 500) # Household

    # Manually register in local map for _get_engine context
    settlement_system.agent_registry.get_agent = MagicMock(side_effect=lambda uid: sender if uid == 101 else (receiver if uid == 102 else None))

    settlement_system.transfer(sender, receiver, 100, "Regular Transfer")

    assert sender.balance_pennies == 900
    assert receiver.balance_pennies == 600

    # Should not call ledger
    mock_ledger.record_monetary_expansion.assert_not_called()
    mock_ledger.record_monetary_contraction.assert_not_called()

def test_transfer_non_m2_to_m2_expansion(settlement_system, mock_ledger):
    """
    Government -> Household (Non-M2 -> M2)
    Should trigger record_monetary_expansion.
    """
    sender = MockAgent(ID_GOVERNMENT, 10000) # Government (Non-M2)
    receiver = MockAgent(101, 500) # Household (M2)

    settlement_system.agent_registry.get_agent = MagicMock(side_effect=lambda uid: sender if uid == ID_GOVERNMENT else (receiver if uid == 101 else None))

    settlement_system.transfer(sender, receiver, 100, "Welfare Payment")

    assert sender.balance_pennies == 9900
    assert receiver.balance_pennies == 600

    # Should record expansion
    mock_ledger.record_monetary_expansion.assert_called_once_with(100, source="Welfare Payment", currency=DEFAULT_CURRENCY)
    mock_ledger.record_monetary_contraction.assert_not_called()

def test_transfer_m2_to_non_m2_contraction(settlement_system, mock_ledger):
    """
    Household -> Government (M2 -> Non-M2)
    Should trigger record_monetary_contraction.
    """
    sender = MockAgent(101, 1000) # Household (M2)
    receiver = MockAgent(ID_GOVERNMENT, 500) # Government (Non-M2)

    settlement_system.agent_registry.get_agent = MagicMock(side_effect=lambda uid: sender if uid == 101 else (receiver if uid == ID_GOVERNMENT else None))

    settlement_system.transfer(sender, receiver, 200, "Tax Payment")

    assert sender.balance_pennies == 800
    assert receiver.balance_pennies == 700

    # Should record contraction
    mock_ledger.record_monetary_contraction.assert_called_once_with(200, source="Tax Payment", currency=DEFAULT_CURRENCY)
    mock_ledger.record_monetary_expansion.assert_not_called()

def test_transfer_non_m2_to_non_m2_no_effect(settlement_system, mock_ledger):
    """
    Government -> Bank (Non-M2 -> Non-M2)
    Should NOT trigger expansion or contraction.
    """
    sender = MockAgent(ID_GOVERNMENT, 10000) # Non-M2
    receiver = MockBank(ID_BANK, 5000) # Non-M2

    settlement_system.agent_registry.get_agent = MagicMock(side_effect=lambda uid: sender if uid == ID_GOVERNMENT else (receiver if uid == ID_BANK else None))

    settlement_system.transfer(sender, receiver, 500, "Bailout")

    assert sender.balance_pennies == 9500
    assert receiver.balance_pennies == 5500

    mock_ledger.record_monetary_expansion.assert_not_called()
    mock_ledger.record_monetary_contraction.assert_not_called()

def test_transaction_processor_ignores_money_creation():
    """
    Verify TransactionProcessor ignores 'money_creation' transactions
    to avoid 'No handler' warnings.
    """
    config = MagicMock()
    tp = TransactionProcessor(config_module=config)

    state = MagicMock(spec=SimulationState)
    state.logger = MagicMock()
    state.transactions = [
        Transaction(
            buyer_id=ID_CENTRAL_BANK, seller_id=101, item_id="currency",
            price=1.0, quantity=100, market_id="settlement",
            transaction_type="money_creation", time=0, total_pennies=100,
            metadata={"executed": True} # This should cause it to be skipped if logic is correct
        )
    ]
    # Also test one WITHOUT executed=True to ensure it is caught by the new exclusion logic
    # But first let's see current behavior.

    # If we add a transaction WITHOUT executed=True, it currently triggers a warning.
    # After fix, it should be ignored.
    tx_unexecuted = Transaction(
        buyer_id=ID_CENTRAL_BANK, seller_id=101, item_id="currency",
        price=1.0, quantity=100, market_id="settlement",
        transaction_type="money_creation", time=0, total_pennies=100
    )
    state.transactions.append(tx_unexecuted)

    # Mock context requirements
    state.agents = {101: MagicMock()}
    state.public_manager = None
    state.bank = MagicMock()
    state.central_bank = MagicMock()
    state.settlement_system = MagicMock()
    state.primary_government = MagicMock()
    state.stock_market = MagicMock()
    state.real_estate_units = []
    state.market_data = {}
    state.inactive_agents = {}
    state.shareholder_registry = MagicMock()
    state.effects_queue = []
    state.time = 0

    tp.execute(state)

    # Before fix: Should warn about "money_creation"
    # After fix: Should NOT warn
    # We assert that warning is NOT called for "money_creation"
    # But currently it IS called. So running this test before fix will fail if we assert_not_called.

    # To demonstrate failure (TDD), we assert that warning IS called for now,
    # and then flip it, OR just assert not called and let it fail.
    # I will assert not called, expecting failure.

    warnings = [call[0][0] for call in state.logger.warning.call_args_list]
    assert not any("No handler for tx type: money_creation" in w for w in warnings), \
        f"Should not warn about money_creation, but got: {warnings}"

def test_money_creation_metadata_executed():
    """
    Verify that create_and_transfer sets 'executed': True in metadata.
    """
    mock_ledger = MagicMock(spec=IMonetaryLedger)
    settlement_system = SettlementSystem()
    settlement_system.set_monetary_ledger(mock_ledger)

    cb = MockAgent(ID_CENTRAL_BANK, 0) # Central Bank can mint
    receiver = MockAgent(101, 0)

    # Mock registry
    settlement_system.agent_registry = MagicMock()
    settlement_system.agent_registry.get_agent.side_effect = lambda uid: cb if uid == ID_CENTRAL_BANK else receiver

    # Use create_and_transfer (acts as minting if source is CB)
    # We need source to be instance of ICentralBank
    class MockCB(MockAgent): # Add ICentralBank marker if needed, but Python mocks are flexible.
        pass
    # Actually SettlementSystem checks isinstance(source, ICentralBank).
    # So we need to mock that.

    # Create a proper Mock that passes isinstance check?
    # Or just patch isinstance? Patching is risky.
    # I'll create a class that inherits ICentralBank protocol or mock it with spec.

    # Actually, simpler: SettlementSystem imports ICentralBank.
    # I can use MagicMock(spec=ICentralBank) but need to implement required methods if checked.
    # SettlementSystem checks: if isinstance(source_authority, ICentralBank)

    # Let's import ICentralBank
    from modules.finance.api import ICentralBank
    class TrueCB(MockAgent, ICentralBank):
        def process_omo_settlement(self, transaction): pass
        def execute_open_market_operation(self, instruction): return []

    cb_agent = TrueCB(ID_CENTRAL_BANK, 0)

    tx = settlement_system.create_and_transfer(cb_agent, receiver, 100, "Minting", 0)

    assert tx is not None
    assert tx.metadata is not None
    assert tx.metadata.get("executed") is True, "Metadata should contain 'executed': True for money_creation"
