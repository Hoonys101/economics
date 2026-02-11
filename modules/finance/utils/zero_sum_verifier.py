from typing import Dict, List, Tuple
import logging
from modules.finance.engine_api import FinancialLedgerDTO
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class ZeroSumVerifier:
    """
    Verifies the integrity of the financial state (Ledger).
    Ensures that financial identities hold (e.g. Assets = Liabilities + Equity).
    Detects leaks or impossible states (negative balances where not allowed).
    MIGRATION: Uses integer pennies.
    """

    @staticmethod
    def verify_ledger_integrity(ledger: FinancialLedgerDTO) -> bool:
        """
        Checks the internal consistency of the Financial Ledger.
        Returns True if valid, False (and logs errors) if invalid.
        """
        is_valid = True

        # 1. Check Banks
        for bank_id, bank_state in ledger.banks.items():
            # Check for negative reserves (Liquidity Crisis / invalid state)
            for curr, amount in bank_state.reserves.items():
                if amount < 0:
                    logger.error(f"INTEGRITY_FAIL | Bank {bank_id} has negative reserves: {amount} {curr}")
                    is_valid = False

            # Check Loan Consistency
            for loan_id, loan in bank_state.loans.items():
                if loan.remaining_principal_pennies > loan.principal_pennies:
                     logger.error(f"INTEGRITY_FAIL | Loan {loan_id} remaining ({loan.remaining_principal_pennies}) > principal ({loan.principal_pennies})")
                     is_valid = False
                if loan.remaining_principal_pennies < 0:
                     logger.error(f"INTEGRITY_FAIL | Loan {loan_id} has negative remaining principal: {loan.remaining_principal_pennies}")
                     is_valid = False

            # Check Deposit Consistency
            for deposit_id, deposit in bank_state.deposits.items():
                if deposit.balance_pennies < 0:
                    logger.error(f"INTEGRITY_FAIL | Deposit {deposit_id} has negative balance: {deposit.balance_pennies}")
                    is_valid = False

            # STRICT ACCOUNTING IDENTITY CHECK: Assets = Liabilities + Equity
            # Assets = Reserves + Loan Principal (or Remaining Principal? Book Value is Remaining)
            total_assets = sum(bank_state.reserves.values()) + sum(l.remaining_principal_pennies for l in bank_state.loans.values())
            # Liabilities = Deposits
            total_liabilities = sum(d.balance_pennies for d in bank_state.deposits.values())
            # Equity = Retained Earnings
            equity = bank_state.retained_earnings_pennies

            # Identity: Assets - (Liabilities + Equity) == 0
            discrepancy = total_assets - (total_liabilities + equity)

            if discrepancy != 0:
                 logger.error(f"INTEGRITY_FAIL | Bank {bank_id} Balance Sheet Mismatch. Assets: {total_assets}, Liab: {total_liabilities}, Equity: {equity}. Discrepancy: {discrepancy}")
                 is_valid = False

        # 2. Check Treasury
        for curr, amount in ledger.treasury.balance.items():
             # Treasury *can* technically run a deficit if we allow it, but usually debt is issued.
             # If balance is negative, it implies overdraft which might be allowed or not.
             if amount < -100000000: # Large overdraft warning
                 logger.warning(f"INTEGRITY_WARN | Treasury has large negative balance: {amount} {curr}")

        return is_valid

    @staticmethod
    def calculate_system_financial_net_worth(ledger: FinancialLedgerDTO) -> int:
        """
        Calculates the net financial worth of the banking system + treasury.
        This is not the Total Economy Net Worth (which includes real assets).
        But useful for tracking leaks in the financial sector.
        """
        total_nw = 0

        for bank_id, bank_state in ledger.banks.items():
            assets = sum(bank_state.reserves.values()) # Simplify: Sum all currencies 1:1 (Wrong but placeholder)
            # Loans are assets
            assets += sum(l.remaining_principal_pennies for l in bank_state.loans.values())

            liabilities = sum(d.balance_pennies for d in bank_state.deposits.values())

            equity = assets - liabilities
            total_nw += equity

        # Treasury Net Worth (Financial)
        treasury_assets = sum(ledger.treasury.balance.values())
        treasury_liabilities = sum(b.face_value_pennies for b in ledger.treasury.bonds.values())

        total_nw += (treasury_assets - treasury_liabilities)

        return total_nw
