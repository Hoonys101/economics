import pytest
from unittest.mock import MagicMock
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from modules.market.api import IHousingTransactionParticipant
from modules.finance.api import IFinancialAgent, IBank, LoanDTO
from simulation.models import Transaction
from modules.system.escrow_agent import EscrowAgent
from modules.common.interfaces import IPropertyOwner
from modules.simulation.api import AgentID

def test_handle_housing_transaction_success():
    handler = HousingTransactionHandler()

    # Setup Context using MagicMock to prevent mock drift
    buyer = MagicMock(spec=IHousingTransactionParticipant)
    buyer.id = AgentID(1)
    buyer.balance_pennies = 100000000
    buyer.current_wage = 500000
    buyer.residing_property_id = None
    buyer.is_homeless = True
    buyer.get_liquid_assets.return_value = 100000000
    buyer.get_balance.return_value = 100000000

    seller = MagicMock(spec=IHousingTransactionParticipant)
    seller.id = AgentID(2)
    seller.balance_pennies = 0
    seller.get_liquid_assets.return_value = 0
    seller.get_balance.return_value = 0

    escrow = EscrowAgent(99)
    bank = MagicMock(spec=IBank)
    bank.id = AgentID(3)

    # Mock Bank methods
    bank.grant_loan.return_value = (
        LoanDTO(
            loan_id="loan_1",
            borrower_id=buyer.id,
            principal_pennies=8000000, # 80k
            remaining_principal_pennies=8000000,
            interest_rate=0.05,
            origination_tick=0,
            lender_id=bank.id,
            term_ticks=300
        ),
        None # credit_tx
    )
    bank.withdraw_for_customer.return_value = True
    bank.get_debt_status.return_value = MagicMock(next_payment_pennies=0, total_outstanding_pennies=0)

    settlement_system = MagicMock()
    settlement_system.transfer.return_value = True # All transfers succeed

    real_estate_units = [MagicMock(id=101, owner_id=seller.id, liens=[])]

    state = MagicMock()
    state.settlement_system = settlement_system
    state.bank = bank
    state.agents = {1: buyer, 2: seller, 99: escrow}
    state.real_estate_units = real_estate_units
    state.config_module = MagicMock()
    state.config_module.housing = {"max_ltv_ratio": 0.8}
    state.time = 0
    state.transaction_queue = []

    tx = Transaction(
        item_id="unit_101",
        buyer_id=buyer.id,
        seller_id=seller.id,
        quantity=1,
        price=100000.0, # 100k dollars
        total_pennies=10000000, # 100k dollars -> 10m pennies
        transaction_type="housing",
        market_id="housing",
        time=0
    )

    result = handler.handle(tx, buyer, seller, state)

    assert result is True
    # Verify Transfers
    # 1. Down Payment: 20% of 10m = 2m pennies
    # 2. Loan Disbursement: 80% of 10m = 8m pennies
    # 3. Final Settlement: 10m pennies

    assert settlement_system.transfer.call_count == 3

    # Check args for transfers
    calls = settlement_system.transfer.call_args_list

    # Down payment
    assert calls[0][0][2] == 2000000
    assert isinstance(calls[0][0][2], int)

    # Loan Disbursement
    assert calls[1][0][2] == 8000000
    assert isinstance(calls[1][0][2], int)

    # Settlement
    assert calls[2][0][2] == 10000000
    assert isinstance(calls[2][0][2], int)

    # Check Bank Grant Loan
    bank.grant_loan.assert_called_once()
    args, kwargs = bank.grant_loan.call_args
    assert kwargs['amount'] == 8000000
    assert isinstance(kwargs['amount'], int)
