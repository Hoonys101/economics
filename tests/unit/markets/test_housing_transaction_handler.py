import pytest
from unittest.mock import MagicMock, call, ANY
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from simulation.models import Transaction
from modules.system.escrow_agent import EscrowAgent
from simulation.core_agents import Household
from modules.market.api import IHousingTransactionParticipant
from modules.common.interfaces import IPropertyOwner
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def handler():
    return HousingTransactionHandler()

@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.settlement_system = MagicMock()
    ctx.bank = MagicMock()
    ctx.config_module = MagicMock()
    # Mock nested structure config_module.housing
    ctx.config_module.housing = {"max_ltv_ratio": 0.8, "mortgage_term_ticks": 300}
    # Also support getattr(config, "housing", {})

    ctx.real_estate_units = []
    ctx.agents = {}
    ctx.logger = MagicMock()
    ctx.time = 0
    ctx.transaction_queue = []

    # Defaults
    ctx.bank.withdraw_for_customer.return_value = True

    return ctx

@pytest.fixture
def buyer():
    # Use IHousingTransactionParticipant as spec to ensure protocol compliance checks pass
    b = MagicMock(spec=IHousingTransactionParticipant)
    b.id = 1

    # Mock assets property to behave like a dict
    b.assets = {DEFAULT_CURRENCY: 100000.0}
    b.get_balance.return_value = 100000.0  # Mock IFinancialAgent.get_balance
    b.current_wage = 100.0 # Required for IMortgageBorrower protocol

    # Protocol Compliance for IHousingTransactionParticipant
    b.owned_properties = []
    b.add_property = MagicMock()
    b.remove_property = MagicMock()
    b.get_all_balances = MagicMock(return_value={DEFAULT_CURRENCY: 100000.0})
    b.total_wealth = 100000.0
    b.deposit = MagicMock()
    b.withdraw = MagicMock()
    b.get_assets_by_currency = MagicMock(return_value={DEFAULT_CURRENCY: 100000.0})
    b.add_item = MagicMock()
    b.remove_item = MagicMock()
    b.get_quantity = MagicMock()
    b.get_quality = MagicMock()
    b.get_all_items = MagicMock()
    b.clear_inventory = MagicMock()
    b.get_agent_data = MagicMock()

    # Also mock _econ_state for legacy checks if any (though handler checks buyer.assets now)
    b._econ_state = MagicMock()
    b._econ_state.assets = {DEFAULT_CURRENCY: 100000.0}
    b._econ_state.owned_properties = []
    b._econ_state.residing_property_id = None
    b._econ_state.is_homeless = True
    b._econ_state.current_wage = 100.0

    return b

@pytest.fixture
def seller():
    # Use IPropertyOwner as spec to ensure protocol compliance checks pass
    s = MagicMock(spec=IPropertyOwner)
    s.id = 2
    s.owned_properties = [101]
    s.remove_property = MagicMock()
    s.add_property = MagicMock()
    return s

@pytest.fixture
def unit():
    u = MagicMock()
    u.id = 101
    u.owner_id = 2
    return u

@pytest.fixture
def escrow_agent():
    e = MagicMock(spec=EscrowAgent)
    e.id = 99
    return e

def test_housing_transaction_success(handler, context, buyer, seller, unit, escrow_agent):
    # Setup
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0, currency=DEFAULT_CURRENCY
    , total_pennies=100000)

    # Mock Settlement Success: DownPayment(True), Disbursement(True), FinalSettlement(True)
    context.settlement_system.transfer.side_effect = [True, True, True]

    # Mock Bank Success
    loan_dto = {"loan_id": "loan_123"}
    context.bank.grant_loan.return_value = (loan_dto, None)

    # Execute
    result = handler.handle(tx, buyer, seller, context)

    # Verify
    assert result is True
    # Down payment (20% of 1000 = 200)
    # Loan (80% of 1000 = 800)

    # 1. Down Payment: Buyer -> Escrow (20000)
    context.settlement_system.transfer.assert_any_call(buyer, escrow_agent, 20000, "escrow_hold:down_payment:unit_101", tick=0, currency=DEFAULT_CURRENCY)

    # 2. Loan Grant called
    context.bank.grant_loan.assert_called()

    # 2b. Deposit Neutralization (Withdrawal)
    context.bank.withdraw_for_customer.assert_called_with(1, 80000)

    # 3. Disbursement: BANK -> Escrow (80000)
    context.settlement_system.transfer.assert_any_call(context.bank, escrow_agent, 80000, "escrow_hold:loan_proceeds:unit_101", tick=0, currency=DEFAULT_CURRENCY)

    # 4. Final Settlement: Escrow -> Seller (100000)
    context.settlement_system.transfer.assert_any_call(escrow_agent, seller, 100000, "final_settlement:unit_101", tick=0, currency=DEFAULT_CURRENCY)

    # 5. Side Effects
    assert unit.owner_id == buyer.id
    # Note: mortgage_id property on unit assumes list traversal, but we appended directly to liens list in handler.
    # We need to verify liens list content.
    has_mortgage = any(l['loan_id'] == "loan_123" and l['lien_type'] == 'MORTGAGE' for l in unit.liens)
    assert has_mortgage

    # Check method calls instead of state mutation for Mocks
    buyer.add_property.assert_called_with(101)

    # Seller might call remove_property or modify list depending on structure
    # Since seller is MagicMock, hasattr(seller, 'remove_property') is True, so it calls it.
    seller.remove_property.assert_called_with(101)

    assert tx.metadata["mortgage_id"] == "loan_123"

def test_housing_transaction_insufficient_down_payment(handler, context, buyer, seller, unit, escrow_agent):
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}
    buyer.assets = {DEFAULT_CURRENCY: 10.0} # Insufficient
    buyer.get_balance.return_value = 10.0

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0, currency=DEFAULT_CURRENCY
    , total_pennies=100000)

    result = handler.handle(tx, buyer, seller, context)
    assert result is False
    context.settlement_system.transfer.assert_not_called()

def test_housing_transaction_loan_rejected(handler, context, buyer, seller, unit, escrow_agent):
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0, currency=DEFAULT_CURRENCY
    , total_pennies=100000)

    # Down payment success
    context.settlement_system.transfer.side_effect = [True, True] # Sequence

    # Bank Rejects
    context.bank.grant_loan.return_value = None

    result = handler.handle(tx, buyer, seller, context)

    assert result is False
    # Verify Compensation: Return Down Payment
    # transfer(escrow, buyer, 200, ...)
    # Call args list:
    # 1. Buyer->Escrow (Down)
    # 2. Escrow->Buyer (Reversal)
    calls = context.settlement_system.transfer.call_args_list
    assert len(calls) >= 2
    assert calls[1][0][0] == escrow_agent
    assert calls[1][0][1] == buyer
    assert "escrow_reversal" in calls[1][0][3]
    # Check kwargs for currency if possible, or use ANY
    # call.kwargs.get('currency') == DEFAULT_CURRENCY

def test_housing_transaction_disbursement_failed(handler, context, buyer, seller, unit, escrow_agent):
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0, currency=DEFAULT_CURRENCY
    , total_pennies=100000)

    # 1. Down Payment Success
    # 2. Loan Proceeds Transfer Fails
    context.settlement_system.transfer.side_effect = [True, False, True]

    loan_dto = {"loan_id": "loan_123"}
    context.bank.grant_loan.return_value = (loan_dto, None)

    result = handler.handle(tx, buyer, seller, context)

    assert result is False
    # Verify Compensation: TERMINATE Loan (not void), Return Down Payment
    context.bank.terminate_loan.assert_called_with("loan_123")

    # Verify withdraw happened
    context.bank.withdraw_for_customer.assert_called()

    # Check transfer calls
    # 1. Buyer->Escrow (Down) [Success]
    # 2. Bank->Escrow (Proceeds) [Fail]
    # 3. Escrow->Buyer (Down Reversal)
    assert context.settlement_system.transfer.call_count == 3
    calls = context.settlement_system.transfer.call_args_list

    # Verify Step 2 was from Bank
    assert calls[1][0][0] == context.bank
    assert calls[1][0][1] == escrow_agent

    # Verify Step 3 was reversal to Buyer
    assert "escrow_reversal" in calls[2][0][3]
