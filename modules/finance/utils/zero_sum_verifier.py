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
                if amount < -0.01: # Allow tiny floating point error
                    logger.error(f"INTEGRITY_FAIL | Bank {bank_id} has negative reserves: {amount} {curr}")
                    is_valid = False

            # Check Loan Consistency
            for loan_id, loan in bank_state.loans.items():
                if loan.remaining_principal > loan.principal + 0.01:
                     logger.error(f"INTEGRITY_FAIL | Loan {loan_id} remaining ({loan.remaining_principal}) > principal ({loan.principal})")
                     is_valid = False
                if loan.remaining_principal < -0.01:
                     logger.error(f"INTEGRITY_FAIL | Loan {loan_id} has negative remaining principal: {loan.remaining_principal}")
                     is_valid = False

            # Check Deposit Consistency
            for deposit_id, deposit in bank_state.deposits.items():
                if deposit.balance < -0.01:
                    logger.error(f"INTEGRITY_FAIL | Deposit {deposit_id} has negative balance: {deposit.balance}")
                    is_valid = False

            # STRICT ACCOUNTING IDENTITY CHECK: Assets = Liabilities + Equity
            # Assets = Reserves + Loan Principal
            total_assets = sum(bank_state.reserves.values()) + sum(l.remaining_principal for l in bank_state.loans.values())
            # Liabilities = Deposits
            total_liabilities = sum(d.balance for d in bank_state.deposits.values())
            # Equity = Retained Earnings
            equity = bank_state.retained_earnings

            # Identity: Assets - (Liabilities + Equity) == 0
            discrepancy = total_assets - (total_liabilities + equity)

            if abs(discrepancy) > 0.01:
                 logger.error(f"INTEGRITY_FAIL | Bank {bank_id} Balance Sheet Mismatch. Assets: {total_assets:.2f}, Liab: {total_liabilities:.2f}, Equity: {equity:.2f}. Discrepancy: {discrepancy:.2f}")
                 is_valid = False

        # 2. Check Treasury
        for curr, amount in ledger.treasury.balance.items():
             # Treasury *can* technically run a deficit if we allow it, but usually debt is issued.
             # If balance is negative, it implies overdraft which might be allowed or not.
             # Let's warn but not fail unless strict mode.
             if amount < -1000000: # Large overdraft warning
                 logger.warning(f"INTEGRITY_WARN | Treasury has large negative balance: {amount} {curr}")

        return is_valid

    @staticmethod
    def calculate_system_financial_net_worth(ledger: FinancialLedgerDTO) -> float:
        """
        Calculates the net financial worth of the banking system + treasury.
        This is not the Total Economy Net Worth (which includes real assets).
        But useful for tracking leaks in the financial sector.
        """
        total_nw = 0.0

        for bank_id, bank_state in ledger.banks.items():
            assets = sum(bank_state.reserves.values()) # Simplify: Sum all currencies 1:1 (Wrong but placeholder)
            # Loans are assets
            assets += sum(l.remaining_principal for l in bank_state.loans.values())

            liabilities = sum(d.balance for d in bank_state.deposits.values())

            equity = assets - liabilities
            total_nw += equity

        # Treasury Net Worth (Financial)
        treasury_assets = sum(ledger.treasury.balance.values())
        treasury_liabilities = sum(b.face_value for b in ledger.treasury.bonds.values())

        total_nw += (treasury_assets - treasury_liabilities)

        return total_nw
