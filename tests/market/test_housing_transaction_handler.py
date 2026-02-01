import pytest
from unittest.mock import MagicMock, call
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from simulation.models import Transaction
from modules.system.escrow_agent import EscrowAgent
from simulation.core_agents import Household

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
    return ctx

@pytest.fixture
def buyer():
    b = MagicMock(spec=Household)
    b.id = 1
    b.assets = 100000.0
    b.owned_properties = []
    b.residing_property_id = None
    b.is_homeless = True
    return b

@pytest.fixture
def seller():
    s = MagicMock()
    s.id = 2
    s.owned_properties = [101]
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
        market_id="housing", transaction_type="housing", time=0
    )

    # Mock Settlement Success: DownPayment(True), Disbursement(True), FinalSettlement(True)
    context.settlement_system.transfer.side_effect = [True, True, True]

    # Mock Bank Success
    loan_dto = MagicMock()
    loan_dto.loan_id = "loan_123"
    context.bank.grant_loan.return_value = (loan_dto, None)

    # Execute
    result = handler.handle(tx, buyer, seller, context)

    # Verify
    assert result is True
    # Down payment (20% of 1000 = 200)
    # Loan (80% of 1000 = 800)

    # 1. Down Payment: Buyer -> Escrow (200)
    context.settlement_system.transfer.assert_any_call(buyer, escrow_agent, 200.0, "escrow_hold:down_payment:unit_101", tick=0)

    # 2. Loan Grant called
    context.bank.grant_loan.assert_called()

    # 3. Disbursement: Buyer -> Escrow (800)
    context.settlement_system.transfer.assert_any_call(buyer, escrow_agent, 800.0, "escrow_hold:loan_proceeds:unit_101", tick=0)

    # 4. Final Settlement: Escrow -> Seller (1000)
    context.settlement_system.transfer.assert_any_call(escrow_agent, seller, 1000.0, "final_settlement:unit_101", tick=0)

    # 5. Side Effects
    assert unit.owner_id == buyer.id
    assert unit.mortgage_id == "loan_123"
    assert 101 in buyer.owned_properties
    assert 101 not in seller.owned_properties
    assert tx.metadata["mortgage_id"] == "loan_123"

def test_housing_transaction_insufficient_down_payment(handler, context, buyer, seller, unit, escrow_agent):
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}
    buyer.assets = 10.0 # Insufficient

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )

    result = handler.handle(tx, buyer, seller, context)
    assert result is False
    context.settlement_system.transfer.assert_not_called()

def test_housing_transaction_loan_rejected(handler, context, buyer, seller, unit, escrow_agent):
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )

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

def test_housing_transaction_disbursement_failed(handler, context, buyer, seller, unit, escrow_agent):
    context.real_estate_units = [unit]
    context.agents = {99: escrow_agent}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )

    # 1. Down Payment Success
    # 2. Loan Proceeds Transfer Fails
    context.settlement_system.transfer.side_effect = [True, False, True]

    loan_dto = MagicMock()
    loan_dto.loan_id = "loan_123"
    context.bank.grant_loan.return_value = (loan_dto, None)

    result = handler.handle(tx, buyer, seller, context)

    assert result is False
    # Verify Compensation: Void Loan, Return Down Payment
    context.bank.void_loan.assert_called_with("loan_123")

    # Check transfer calls
    # 1. Buyer->Escrow (Down) [Success]
    # 2. Buyer->Escrow (Proceeds) [Fail]
    # 3. Escrow->Buyer (Down Reversal)
    assert context.settlement_system.transfer.call_count == 3
    calls = context.settlement_system.transfer.call_args_list
    assert "escrow_reversal" in calls[2][0][3]
