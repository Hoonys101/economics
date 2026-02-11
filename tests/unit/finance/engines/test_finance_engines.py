import pytest
from unittest.mock import MagicMock
from modules.finance.engine_api import (
    FinancialLedgerDTO, BankStateDTO, LoanStateDTO, DepositStateDTO, TreasuryStateDTO,
    LoanApplicationDTO, LoanDecisionDTO, LiquidationRequestDTO
)
from modules.finance.engines.loan_risk_engine import LoanRiskEngine
from modules.finance.engines.loan_booking_engine import LoanBookingEngine
from modules.finance.engines.liquidation_engine import LiquidationEngine
from modules.finance.engines.debt_servicing_engine import DebtServicingEngine
from modules.finance.utils.zero_sum_verifier import ZeroSumVerifier
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def empty_ledger():
    return FinancialLedgerDTO(
        current_tick=0,
        treasury=TreasuryStateDTO(government_id="GOV"),
        banks={
            "BANK1": BankStateDTO(bank_id="BANK1", reserves={DEFAULT_CURRENCY: 10000.0}, base_rate=0.03)
        }
    )

def test_loan_risk_engine_assess_approved(empty_ledger):
    engine = LoanRiskEngine()
    app = LoanApplicationDTO(borrower_id="FIRM1", amount=1000.0, borrower_profile={"credit_score": 700, "income": 5000})

    decision = engine.assess(app, empty_ledger)
    assert decision.is_approved
    assert decision.interest_rate >= 0.03

def test_loan_risk_engine_assess_denied(empty_ledger):
    engine = LoanRiskEngine()
    app = LoanApplicationDTO(borrower_id="FIRM2", amount=1000.0, borrower_profile={"credit_score": 200})

    decision = engine.assess(app, empty_ledger)
    assert not decision.is_approved
    assert decision.rejection_reason == "Credit Score too low"

def test_loan_booking_engine_grant_loan(empty_ledger):
    engine = LoanBookingEngine()
    app = LoanApplicationDTO(borrower_id="FIRM1", amount=1000.0, borrower_profile={"preferred_lender_id": "BANK1"})
    decision = LoanDecisionDTO(is_approved=True, interest_rate=0.05)

    output = engine.grant_loan(app, decision, empty_ledger)

    # Check Ledger Update
    bank = output.updated_ledger.banks["BANK1"]
    assert len(bank.loans) == 1
    loan = next(iter(bank.loans.values()))
    assert loan.principal == 1000.0
    assert loan.borrower_id == "FIRM1"

    # Check Deposit Created
    assert len(bank.deposits) == 1
    deposit = next(iter(bank.deposits.values()))
    assert deposit.balance == 1000.0
    assert deposit.customer_id == "FIRM1"

    # Check Transaction
    assert len(output.generated_transactions) == 1
    tx = output.generated_transactions[0]
    assert tx.transaction_type == "credit_creation"
    assert tx.price == 1000.0

def test_liquidation_engine_liquidate(empty_ledger):
    # Setup Firm Loan
    bank = empty_ledger.banks["BANK1"]
    loan = LoanStateDTO("L1", "FIRM1", "BANK1", 1000.0, 1000.0, 0.05, 0, 10)
    bank.loans["L1"] = loan

    engine = LiquidationEngine()
    req = LiquidationRequestDTO("FIRM1", inventory_value=500.0, capital_value=0.0, outstanding_debt=1000.0)

    output = engine.liquidate(req, empty_ledger)

    # Check Debt Settlement (Partial)
    updated_bank = output.updated_ledger.banks["BANK1"]
    updated_loan = updated_bank.loans["L1"]

    # Inventory sold for 50% -> 250.0
    # Loan reduced by 250.0 -> 750.0 remaining
    # And then defaulted?
    # LiquidationEngine logic:
    # 1. Sell Inventory -> 250.0
    # 2. Pay Loan -> 250.0 (Remaining 750.0)
    # 3. Default Remaining -> 750.0

    # Wait, my logic for LiquidationEngine sets `loan.is_defaulted = True` if remaining > 0.
    # And keeps remaining principal? Or writes it off?
    # Logic: `loan.remaining_principal = 0` (Write-off) but generate `loan_default` transaction.

    assert updated_loan.is_defaulted
    assert updated_loan.remaining_principal == 0.0 # Wrote off

    # Check Transactions
    tx_types = [tx.transaction_type for tx in output.generated_transactions]
    assert "liquidation_sale" in tx_types
    assert "loan_repayment_liquidation" in tx_types
    assert "loan_default" in tx_types

def test_debt_servicing_engine(empty_ledger):
    bank = empty_ledger.banks["BANK1"]
    # Loan
    loan = LoanStateDTO("L1", "FIRM1", "BANK1", 1000.0, 1000.0, 0.05, 0, 10) # 5% annual
    bank.loans["L1"] = loan
    # Deposit (for payment)
    dep_id = "DEP_FIRM1_BANK1"
    deposit = DepositStateDTO(dep_id, "FIRM1", 100.0, 0.0, DEFAULT_CURRENCY)
    bank.deposits[dep_id] = deposit

    engine = DebtServicingEngine()
    empty_ledger.current_tick = 1

    output = engine.service_all_debt(empty_ledger)

    # Check Interest Payment
    # Interest = 1000 * 0.05 / 365 = 0.137
    expected_interest = 1000.0 * 0.05 / 365.0

    updated_deposit = output.updated_ledger.banks["BANK1"].deposits[dep_id]
    assert updated_deposit.balance < 100.0
    assert updated_deposit.balance == pytest.approx(100.0 - expected_interest)

    # Check Transaction
    tx = output.generated_transactions[0]
    assert tx.transaction_type == "loan_interest"
    assert tx.price == pytest.approx(expected_interest)

def test_zero_sum_verifier(empty_ledger):
    # Valid State
    assert ZeroSumVerifier.verify_ledger_integrity(empty_ledger)

    # Invalid State (Negative Reserve)
    empty_ledger.banks["BANK1"].reserves[DEFAULT_CURRENCY] = -100.0
    assert not ZeroSumVerifier.verify_ledger_integrity(empty_ledger)

    # Invalid State (Loan > Principal)
    empty_ledger.banks["BANK1"].reserves[DEFAULT_CURRENCY] = 100.0 # Reset
    loan = LoanStateDTO("L1", "FIRM1", "BANK1", 1000.0, 1100.0, 0.05, 0, 10) # Remaining > Principal
    empty_ledger.banks["BANK1"].loans["L1"] = loan
    assert not ZeroSumVerifier.verify_ledger_integrity(empty_ledger)
