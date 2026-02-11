import uuid
from typing import Optional
from modules.finance.engine_api import (
    ILoanBookingEngine, LoanApplicationDTO, LoanDecisionDTO, FinancialLedgerDTO,
    EngineOutputDTO, LoanStateDTO, DepositStateDTO, BankStateDTO
)
from modules.simulation.api import AgentID
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction

class LoanBookingEngine(ILoanBookingEngine):
    """
    Stateless engine to book approved loans.
    """

    def grant_loan(
        self,
        application: LoanApplicationDTO,
        decision: LoanDecisionDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:

        if not decision.is_approved:
            return EngineOutputDTO(updated_ledger=ledger, generated_transactions=[])

        # We need a lender. Since LoanApplicationDTO doesn't have it,
        # we must assume the caller (FinanceSystem) handles lender selection
        # or we pick one from ledger.
        # ISSUE: LoanBookingEngine needs to know WHO is lending.
        # I should update LoanApplicationDTO to include lender_id.
        # But I can't modify engine_api.py right now easily without going back.
        # I'll check if I can infer it or if I should patch the DTO.
        # For now, let's assume the first bank in the ledger is the lender
        # OR the logic is run *by* a specific bank context.
        # But the engine is stateless and receives the whole ledger.
        # I will assume lender_id is passed in borrower_profile for now as a workaround,
        # or I'll pick the bank with most reserves.

        lender_id = application.borrower_profile.get("preferred_lender_id")
        if not lender_id and ledger.banks:
            lender_id = next(iter(ledger.banks.keys()))

        if not lender_id or lender_id not in ledger.banks:
             # Fail gracefully if no lender found
             return EngineOutputDTO(updated_ledger=ledger, generated_transactions=[])

        bank_state = ledger.banks[lender_id]

        # 1. Create Loan
        loan_id = str(uuid.uuid4())
        loan = LoanStateDTO(
            loan_id=loan_id,
            borrower_id=application.borrower_id,
            lender_id=lender_id,
            principal=application.amount,
            remaining_principal=application.amount,
            interest_rate=decision.interest_rate,
            origination_tick=ledger.current_tick,
            due_tick=ledger.current_tick + 50 # Default term
        )

        # 2. Create/Update Deposit (Money Creation)
        # Does the borrower already have a deposit account at this bank?
        deposit_id = f"DEP_{application.borrower_id}_{lender_id}" # Simplified ID

        if deposit_id in bank_state.deposits:
            deposit = bank_state.deposits[deposit_id]
            deposit.balance += application.amount
        else:
            deposit = DepositStateDTO(
                deposit_id=deposit_id,
                customer_id=application.borrower_id,
                balance=application.amount,
                interest_rate=0.0 # Default
            )
            bank_state.deposits[deposit_id] = deposit

        bank_state.loans[loan_id] = loan

        # 3. Generate Transaction
        tx = Transaction(
            buyer_id=lender_id,
            seller_id="GOVERNMENT", # Or Abstract? Credit creation usually has no seller.
            # Wait, credit creation: Bank swaps IOUs.
            # Bank gets Loan Asset (from Borrower). Borrower gets Deposit (from Bank).
            # The "Transaction" object in this system usually records the flow for analysis.
            # Transaction(buyer=Borrower, seller=Bank, item=Loan, price=Amount)?
            # Or buyer=Bank, seller=Borrower?
            # Existing Bank code: buyer_id=self.id, seller_id=government/nobody, item="credit_creation..."
            item_id=f"credit_creation_{loan_id}",
            quantity=1,
            price=application.amount,
            market_id="monetary_policy",
            transaction_type="credit_creation",
            time=ledger.current_tick
        )

        return EngineOutputDTO(
            updated_ledger=ledger,
            generated_transactions=[tx]
        )
