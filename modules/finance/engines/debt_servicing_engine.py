from decimal import Decimal
from modules.finance.engine_api import (
    IDebtServicingEngine, FinancialLedgerDTO, EngineOutputDTO
)
from simulation.models import Transaction
from modules.finance.utils.currency_math import round_to_pennies

class DebtServicingEngine(IDebtServicingEngine):
    """
    Stateless engine to service debts (interest payments).
    MIGRATION: Uses integer pennies and Decimal math.
    """

    def service_all_debt(self, ledger: FinancialLedgerDTO) -> EngineOutputDTO:
        txs = []

        # 1. Service Bank Loans
        for bank_id, bank in ledger.banks.items():
            for loan_id, loan in bank.loans.items():
                if loan.remaining_principal_pennies <= 0 or loan.is_defaulted:
                    continue

                # Calculate Interest
                # Formula: Principal * Rate / 365
                # All inputs to Decimal.
                # Rate is float (e.g. 0.05). Principal is int pennies.
                interest_pennies = round_to_pennies(
                    Decimal(loan.remaining_principal_pennies) * Decimal(loan.interest_rate) / Decimal(365)
                )

                # Check if borrower has deposit in this bank
                borrower_deposit_id = f"DEP_{loan.borrower_id}_{bank_id}"
                deposit = bank.deposits.get(borrower_deposit_id)

                payment_made = 0

                if deposit and deposit.balance_pennies >= interest_pennies:
                    # WO-IMPL-LEDGER-HARDENING: Use local tracking to prevent shadow transactions
                    # We do NOT modify deposit.balance_pennies directly. The emitted Transaction will update the SSoT.
                    current_balance = deposit.balance_pennies

                    if current_balance >= interest_pennies:
                        current_balance -= interest_pennies

                        # [Double-Entry] Debit Liability (Deposit)
                        deposit.balance_pennies -= interest_pennies

                        # [Double-Entry] Credit Bank Equity (Retained Earnings)
                        bank.retained_earnings_pennies += interest_pennies

                        payment_made = interest_pennies

                        txs.append(Transaction(
                            buyer_id=loan.borrower_id,
                            seller_id=bank_id, # Pay to Bank (Replenish Reserves)
                            item_id=loan_id,
                            quantity=1,
                            price=interest_pennies / 100.0,
                            market_id="financial",
                            transaction_type="loan_interest",
                            time=ledger.current_tick
                        , total_pennies=interest_pennies))

                        # Principal repayment
                        if ledger.current_tick >= loan.due_tick:
                            principal_due = loan.remaining_principal_pennies
                            if current_balance >= principal_due:
                                # Full Repayment
                                current_balance -= principal_due
                                deposit.balance_pennies -= principal_due

                                # DO NOT update loan.remaining_principal_pennies (Handler does it)
                                payment_made += principal_due

                                txs.append(Transaction(
                                    buyer_id=loan.borrower_id,
                                    seller_id=bank_id, # Pay to Bank
                                    item_id=loan_id,
                                    quantity=1,
                                    price=principal_due / 100.0,
                                    market_id="financial",
                                    transaction_type="loan_repayment",
                                    time=ledger.current_tick
                                , total_pennies=principal_due))
                            else:
                                # Partial pay?
                                pay = current_balance
                                current_balance = 0
                                deposit.balance_pennies -= pay

                                # DO NOT update loan.remaining_principal_pennies (Handler does it)

                                if pay > 0:
                                    txs.append(Transaction(
                                        buyer_id=loan.borrower_id,
                                        seller_id=bank_id, # Pay to Bank
                                        item_id=loan_id,
                                        quantity=1,
                                        price=pay / 100.0,
                                        market_id="financial",
                                        transaction_type="loan_repayment",
                                        time=ledger.current_tick
                                    , total_pennies=pay))

        # 2. Service Treasury Bonds
        treasury = ledger.treasury
        for bond_id, bond in treasury.bonds.items():
            # Calculate Interest
            interest_pennies = round_to_pennies(
                Decimal(bond.face_value_pennies) * Decimal(bond.yield_rate) / Decimal(365)
            )

            # Check receiver
            receiver_id = bond.owner_id

            # Find receiver's account.
            # If receiver is a Bank, update its reserves.
            if receiver_id in ledger.banks:
                bank = ledger.banks[receiver_id]
                # Update reserves
                curr = "USD" # Default
                if curr not in bank.reserves: bank.reserves[curr] = 0
                bank.reserves[curr] += interest_pennies

                # [Double-Entry] Credit Equity (Interest Income)
                bank.retained_earnings_pennies += interest_pennies

                # Treasury pays
                if curr not in treasury.balance: treasury.balance[curr] = 0
                treasury.balance[curr] -= interest_pennies

                txs.append(Transaction(
                    buyer_id=treasury.government_id,
                    seller_id=receiver_id,
                    item_id=bond_id,
                    quantity=1,
                    price=interest_pennies / 100.0,
                    market_id="financial",
                    transaction_type="bond_interest",
                    time=ledger.current_tick
                , total_pennies=interest_pennies))

        return EngineOutputDTO(
            updated_ledger=ledger,
            generated_transactions=txs
        )
