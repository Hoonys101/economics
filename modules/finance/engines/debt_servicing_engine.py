from modules.finance.engine_api import (
    IDebtServicingEngine, FinancialLedgerDTO, EngineOutputDTO
)
from simulation.models import Transaction

class DebtServicingEngine(IDebtServicingEngine):
    """
    Stateless engine to service debts (interest payments).
    """

    def service_all_debt(self, ledger: FinancialLedgerDTO) -> EngineOutputDTO:
        txs = []

        # 1. Service Bank Loans
        for bank_id, bank in ledger.banks.items():
            for loan_id, loan in bank.loans.items():
                if loan.remaining_principal <= 0 or loan.is_defaulted:
                    continue

                # Calculate Interest
                interest = loan.remaining_principal * loan.interest_rate / 365.0 # Daily?

                # Check if borrower has deposit in this bank
                # (Simplification: Only auto-deduct if funds exist in same bank)
                # In real system, might trigger inter-bank transfer.

                borrower_deposit_id = f"DEP_{loan.borrower_id}_{bank_id}"
                # Or search for any deposit by this borrower
                deposit = bank.deposits.get(borrower_deposit_id)

                payment_made = 0.0

                if deposit and deposit.balance >= interest:
                    deposit.balance -= interest
                    # [Double-Entry] Credit Bank Equity (Retained Earnings)
                    # Liability (Deposit) decreases, Equity increases. Assets unchanged.
                    bank.retained_earnings += interest

                    payment_made = interest

                    txs.append(Transaction(
                        buyer_id=loan.borrower_id,
                        seller_id=bank_id,
                        item_id=loan_id,
                        quantity=1,
                        price=interest,
                        market_id="financial",
                        transaction_type="loan_interest",
                        time=ledger.current_tick
                    ))

                    # Principal repayment (Amortization) - Optional/Simple
                    # Let's say 1% of principal per tick? Or just interest only for now?
                    # Bank code had due_tick.
                    # If due_tick reached, pay principal.
                    if ledger.current_tick >= loan.due_tick:
                        principal_due = loan.remaining_principal
                        if deposit.balance >= principal_due:
                            deposit.balance -= principal_due
                            loan.remaining_principal = 0
                            payment_made += principal_due

                            txs.append(Transaction(
                                buyer_id=loan.borrower_id,
                                seller_id=bank_id,
                                item_id=loan_id,
                                quantity=1,
                                price=principal_due,
                                market_id="financial",
                                transaction_type="loan_repayment",
                                time=ledger.current_tick
                            ))
                        else:
                            # Partial pay?
                            pay = deposit.balance
                            deposit.balance = 0
                            loan.remaining_principal -= pay

                            txs.append(Transaction(
                                buyer_id=loan.borrower_id,
                                seller_id=bank_id,
                                item_id=loan_id,
                                quantity=1,
                                price=pay,
                                market_id="financial",
                                transaction_type="loan_repayment",
                                time=ledger.current_tick
                            ))
                            # Mark default if not fully paid?
                            # loan.is_defaulted = True # Let's be lenient for now or use grace period

        # 2. Service Treasury Bonds
        # Treasury pays coupons to Bond Holders
        treasury = ledger.treasury
        for bond_id, bond in treasury.bonds.items():
            # Simple interest every tick? Or periodic?
            # Let's assume daily accrual/payment for simplicity
            interest = bond.face_value * bond.yield_rate / 365.0

            # Treasury pays. Treasury balance?
            # Treasury balance is in ledger.treasury.balance (Dict[Currency, float])
            # Assuming DEFAULT_CURRENCY

            # Check receiver
            receiver_id = bond.owner_id

            # Find receiver's account.
            # If receiver is a Bank, update its reserves.
            if receiver_id in ledger.banks:
                bank = ledger.banks[receiver_id]
                # Update reserves
                # We need to know currency.
                curr = "USD" # Default
                if curr not in bank.reserves: bank.reserves[curr] = 0.0
                bank.reserves[curr] += interest

                # [Double-Entry] Credit Equity (Interest Income)
                # Asset (Reserves) Up, Equity (Retained Earnings) Up
                bank.retained_earnings += interest

                # Treasury pays
                if curr not in treasury.balance: treasury.balance[curr] = 0.0
                treasury.balance[curr] -= interest

                txs.append(Transaction(
                    buyer_id=treasury.government_id,
                    seller_id=receiver_id,
                    item_id=bond_id,
                    quantity=1,
                    price=interest,
                    market_id="financial",
                    transaction_type="bond_interest",
                    time=ledger.current_tick
                ))

        return EngineOutputDTO(
            updated_ledger=ledger,
            generated_transactions=txs
        )
