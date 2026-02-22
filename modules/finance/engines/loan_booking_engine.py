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
    MIGRATION: Uses integer pennies.
    """

    def grant_loan(
        self,
        application: LoanApplicationDTO,
        decision: LoanDecisionDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:

        if not decision.is_approved:
            return EngineOutputDTO(updated_ledger=ledger, generated_transactions=[])

        lender_id = application.lender_id

        if not lender_id:
             lender_id = application.borrower_profile.get("preferred_lender_id")
             if not lender_id and ledger.banks:
                 lender_id = next(iter(ledger.banks.keys()))

        if not lender_id or lender_id not in ledger.banks:
             return EngineOutputDTO(updated_ledger=ledger, generated_transactions=[])

        bank_state = ledger.banks[lender_id]

        # 1. Create Loan
        loan_id = str(uuid.uuid4())
        loan = LoanStateDTO(
            loan_id=loan_id,
            borrower_id=application.borrower_id,
            lender_id=lender_id,
            principal_pennies=application.amount_pennies,
            remaining_principal_pennies=application.amount_pennies,
            interest_rate=decision.interest_rate,
            origination_tick=ledger.current_tick,
            due_tick=ledger.current_tick + 50 # Default term
        )

        # 2. Create/Update Deposit (Money Creation)
        deposit_id = f"DEP_{application.borrower_id}_{lender_id}" # Simplified ID

        if deposit_id in bank_state.deposits:
            deposit = bank_state.deposits[deposit_id]
            deposit.balance_pennies += application.amount_pennies
        else:
            deposit = DepositStateDTO(
                deposit_id=deposit_id,
                owner_id=application.borrower_id, # Use owner_id as primary
                customer_id=application.borrower_id, # Legacy/Alias
                balance_pennies=application.amount_pennies,
                interest_rate=0.0 # Default
            )
            bank_state.deposits[deposit_id] = deposit

        bank_state.loans[loan_id] = loan

        # 3. Generate Transaction
        tx = Transaction(
            buyer_id=lender_id,
            seller_id="GOVERNMENT",
            item_id=f"credit_creation_{loan_id}",
            quantity=application.amount_pennies, # Int quantity
            price=1.0,
            market_id="monetary_policy",
            transaction_type="credit_creation",
            time=ledger.current_tick
        , total_pennies=application.amount_pennies)

        return EngineOutputDTO(
            updated_ledger=ledger,
            generated_transactions=[tx]
        )
