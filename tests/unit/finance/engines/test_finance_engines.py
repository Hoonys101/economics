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
from modules.finance.utils.currency_math import round_to_pennies
from decimal import Decimal

@pytest.fixture
def empty_ledger():
    return FinancialLedgerDTO(
        current_tick=0,
        treasury=TreasuryStateDTO(government_id="GOV"),
        banks={
            # Initial Reserves (1000000 pennies = 10000.00)
            "BANK1": BankStateDTO(
                bank_id="BANK1",
                reserves={DEFAULT_CURRENCY: 1000000},
                base_rate=0.03,
                retained_earnings_pennies=1000000
            )
        }
    )

def test_loan_risk_engine_assess_approved(empty_ledger):
    engine = LoanRiskEngine()
    # Amount 1000.00 -> 100000 pennies
    app = LoanApplicationDTO(borrower_id="FIRM1", lender_id="BANK1", amount_pennies=100000, borrower_profile={"credit_score": 700, "income": 500000})

    decision = engine.assess(app, empty_ledger)
    assert decision.is_approved
    assert decision.interest_rate >= 0.03

def test_loan_risk_engine_assess_denied(empty_ledger):
    engine = LoanRiskEngine()
    app = LoanApplicationDTO(borrower_id="FIRM2", lender_id="BANK1", amount_pennies=100000, borrower_profile={"credit_score": 200})

    decision = engine.assess(app, empty_ledger)
    assert not decision.is_approved
    assert decision.rejection_reason == "Credit Score too low"

def test_loan_booking_engine_grant_loan(empty_ledger):
    engine = LoanBookingEngine()
    app = LoanApplicationDTO(borrower_id="FIRM1", lender_id="BANK1", amount_pennies=100000, borrower_profile={"preferred_lender_id": "BANK1"})
    decision = LoanDecisionDTO(is_approved=True, interest_rate=0.05)

    output = engine.grant_loan(app, decision, empty_ledger)

    # Check Ledger Update
    bank = output.updated_ledger.banks["BANK1"]
    assert len(bank.loans) == 1
    loan = next(iter(bank.loans.values()))
    assert loan.principal_pennies == 100000
    assert loan.borrower_id == "FIRM1"

    # Check Deposit Created
    assert len(bank.deposits) == 1
    deposit = next(iter(bank.deposits.values()))
    assert deposit.balance_pennies == 100000
    assert deposit.customer_id == "FIRM1"

    # Check Transaction
    assert len(output.generated_transactions) == 1
    tx = output.generated_transactions[0]
    assert tx.transaction_type == "credit_creation"
    assert tx.quantity == 100000 # Quantity is amount in pennies now

    # Integrity Check
    assert ZeroSumVerifier.verify_ledger_integrity(output.updated_ledger)

def test_liquidation_engine_liquidate(empty_ledger):
    # Setup Firm Loan
    bank = empty_ledger.banks["BANK1"]
    # 1000.00 loan -> 100000 pennies
    loan = LoanStateDTO("L1", "FIRM1", "BANK1", 100000, 100000, 0.05, 0, 10)
    bank.loans["L1"] = loan
    # Balance the ledger: Loan created from Reserves (Asset swap logic, effectively)
    # Assets: Reserves (900000) + Loan (100000) = 1000000
    # Equity: 1000000
    bank.reserves[DEFAULT_CURRENCY] -= 100000

    initial_retained_earnings = bank.retained_earnings_pennies

    engine = LiquidationEngine()
    # Inventory 500.00 -> 50000 pennies
    req = LiquidationRequestDTO("FIRM1", inventory_value_pennies=50000, capital_value_pennies=0, outstanding_debt_pennies=100000)

    output = engine.liquidate(req, empty_ledger)

    # Check Debt Settlement (Partial)
    updated_bank = output.updated_ledger.banks["BANK1"]
    updated_loan = updated_bank.loans["L1"]

    # Inventory sold for 50% -> 25000 pennies. Loan reduced by 25000. Remaining 75000 written off.
    assert updated_loan.is_defaulted
    assert updated_loan.remaining_principal_pennies == 0 # Wrote off

    # Check Retained Earnings Reduction (Write-off)
    expected_writeoff = 75000
    assert updated_bank.retained_earnings_pennies == initial_retained_earnings - expected_writeoff

    # Check Transactions
    tx_types = [tx.transaction_type for tx in output.generated_transactions]
    assert "liquidation_sale" in tx_types
    assert "loan_repayment_liquidation" in tx_types
    assert "loan_default" in tx_types

    # Integrity Check
    assert ZeroSumVerifier.verify_ledger_integrity(output.updated_ledger)

def test_debt_servicing_engine(empty_ledger):
    bank = empty_ledger.banks["BANK1"]
    # Loan
    loan = LoanStateDTO("L1", "FIRM1", "BANK1", 100000, 100000, 0.05, 0, 10) # 5% annual
    bank.loans["L1"] = loan
    # Deposit (for payment)
    dep_id = "DEP_FIRM1_BANK1"
    deposit = DepositStateDTO(dep_id, "FIRM1", 10000, 0.0, DEFAULT_CURRENCY) # 100.00
    bank.deposits[dep_id] = deposit

    # Balance the ledger manually
    # Assets: Reserves (1000000) + Loan (100000) = 1100000
    # Liabilities: Deposit (10000)
    # Equity: 1000000
    # Discrepancy: 1100000 - 1010000 = 90000
    # Withdraw 90000 from reserves to balance
    bank.reserves[DEFAULT_CURRENCY] -= 90000

    initial_retained = bank.retained_earnings_pennies

    engine = DebtServicingEngine()
    empty_ledger.current_tick = 1

    output = engine.service_all_debt(empty_ledger)

    # Check Interest Payment
    # 100000 * 0.05 / 365 = 13.69 pennies -> 14 pennies
    expected_interest = round_to_pennies(Decimal(100000) * Decimal("0.05") / Decimal(365))
    # 14 pennies

    updated_bank = output.updated_ledger.banks["BANK1"]
    updated_deposit = updated_bank.deposits[dep_id]
    assert updated_deposit.balance_pennies < 10000
    assert updated_deposit.balance_pennies == 10000 - expected_interest

    # Verify Double Entry: Interest credited to Retained Earnings
    assert updated_bank.retained_earnings_pennies == initial_retained + expected_interest

    # Check Transaction
    tx = output.generated_transactions[0]
    assert tx.transaction_type == "loan_interest"
    assert tx.total_pennies == expected_interest

    # Integrity Check
    assert ZeroSumVerifier.verify_ledger_integrity(output.updated_ledger)

def test_zero_sum_verifier(empty_ledger):
    # Valid State
    assert ZeroSumVerifier.verify_ledger_integrity(empty_ledger)

    # Invalid State (Negative Reserve) - Wait, negative reserves might be allowed in some contexts (overdraft),
    # but Equity must match Assets-Liabilities.
    # If reserves are -100, Assets decrease. Equity must decrease.
    empty_ledger.banks["BANK1"].reserves[DEFAULT_CURRENCY] = -100
    # Equity is still 1000000. Assets (Reserves+Loans) = -100 + 0 = -100.
    # Liabilities = 0.
    # Equity != Assets - Liabilities.
    assert not ZeroSumVerifier.verify_ledger_integrity(empty_ledger)

    # Invalid State (Loan > Principal)
    empty_ledger.banks["BANK1"].reserves[DEFAULT_CURRENCY] = 1000000 # Reset
    loan = LoanStateDTO("L1", "FIRM1", "BANK1", 100000, 110000, 0.05, 0, 10) # Remaining > Principal
    empty_ledger.banks["BANK1"].loans["L1"] = loan
    # This check (Remaining > Principal) is domain logic, not accounting identity.
    # ZeroSumVerifier checks Assets = Liabilities + Equity.
    # Loan Asset Value = Remaining Principal? Or Principal?
    # Usually Remaining Principal is the asset value on books.
    # If remaining increases, Asset increases. Equity must increase.
    # Here Equity is unchanged. So it should fail.
    assert not ZeroSumVerifier.verify_ledger_integrity(empty_ledger)
