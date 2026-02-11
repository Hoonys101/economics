import pytest
from unittest.mock import MagicMock, patch
from simulation.bank import Bank
from modules.finance.api import IFinanceSystem, LoanInfoDTO
from modules.simulation.api import AgentID
from modules.finance.engine_api import FinancialLedgerDTO, BankStateDTO, DepositStateDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction

@pytest.fixture
def mock_finance_system():
    fs = MagicMock(spec=IFinanceSystem)
    # Setup default ledger
    ledger = FinancialLedgerDTO(
        current_tick=0,
        banks={},
        treasury=MagicMock()
    )
    fs.ledger = ledger
    return fs

@pytest.fixture
def bank(mock_finance_system):
    config_manager = MagicMock()
    config_manager.get.return_value = 0.03

    bank = Bank(
        id=1,
        initial_assets=100000, # 1000.00 -> 100000 pennies
        config_manager=config_manager
    )
    bank.set_finance_system(mock_finance_system)

    # Setup Bank State in Ledger
    mock_finance_system.ledger.banks[1] = BankStateDTO(
        bank_id=1,
        reserves={DEFAULT_CURRENCY: 100000},
        base_rate=0.03,
        retained_earnings_pennies=100000
    )

    return bank

def test_bank_assets_delegation(bank, mock_finance_system):
    # Should get from Ledger
    assert bank.assets == 100000

    # Modify Ledger
    mock_finance_system.ledger.banks[1].reserves[DEFAULT_CURRENCY] = 200000
    assert bank.assets == 200000

def test_bank_deposit_delegation(bank, mock_finance_system):
    # Deposit adds to reserves in Ledger
    bank.deposit(50000) # 500.00
    assert mock_finance_system.ledger.banks[1].reserves[DEFAULT_CURRENCY] == 150000

def test_bank_withdraw_delegation(bank, mock_finance_system):
    bank.withdraw(20000) # 200.00
    assert mock_finance_system.ledger.banks[1].reserves[DEFAULT_CURRENCY] == 80000

def test_grant_loan_delegation(bank, mock_finance_system):
    # Setup Mock Return
    mock_loan = LoanInfoDTO(
        loan_id="L1", borrower_id=2, original_amount=10000, outstanding_balance=10000,
        interest_rate=0.05, origination_tick=0, due_tick=10
    )
    mock_tx = Transaction(buyer_id=1, seller_id=2, item_id="L1", quantity=10000, price=1.0, market_id="m", transaction_type="credit_creation", time=0)

    mock_finance_system.process_loan_application.return_value = (mock_loan, [mock_tx])

    result = bank.grant_loan(borrower_id=2, amount=10000, interest_rate=0.05)

    assert result is not None
    assert result[0] == mock_loan
    assert result[1] == mock_tx

    # Check call args (int check)
    args, kwargs = mock_finance_system.process_loan_application.call_args
    assert kwargs['amount'] == 10000

def test_withdraw_for_customer(bank, mock_finance_system):
    # Setup Deposit in Ledger
    customer_id = 2
    dep_id = f"DEP_{customer_id}_{bank.id}"
    deposit = DepositStateDTO(dep_id, customer_id, 50000, 0.0) # 500.00
    mock_finance_system.ledger.banks[bank.id].deposits[dep_id] = deposit

    # Act
    success = bank.withdraw_for_customer(customer_id, 20000) # 200.00

    assert success
    assert deposit.balance_pennies == 30000

    # Fail case
    success_fail = bank.withdraw_for_customer(customer_id, 40000) # 400.00
    assert not success_fail
    assert deposit.balance_pennies == 30000

def test_run_tick_delegates_to_service_debt(bank, mock_finance_system):
    mock_tx = MagicMock(spec=Transaction)
    mock_finance_system.service_debt.return_value = [mock_tx]

    txs = bank.run_tick({}, current_tick=10)

    mock_finance_system.service_debt.assert_called_with(10)
    assert mock_tx in txs
