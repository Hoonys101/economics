
import sys
import os
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from simulation.models import Transaction, Order
from simulation.bank import Loan

def reproduce_leaks():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("REPRO")

    sim = create_simulation()

    # --- Helper to calculate M2 ---
    def get_m2():
        h_assets = sum(h.assets for h in sim.households if h.is_active)
        f_assets = sum(f.assets for f in sim.firms if f.is_active)
        gov_assets = sim.government.assets
        bank_assets = sim.bank.assets
        reflux_bal = sim.reflux_system.balance if hasattr(sim, 'reflux_system') else 0.0
        return h_assets + f_assets + gov_assets + bank_assets + reflux_bal

    logger.info("--- Starting Reproduction ---")
    initial_m2 = get_m2()
    logger.info(f"Initial M2: {initial_m2}")

    # --- Test 1: Bank Loan Default (Hypothesis B) ---
    logger.info("\n--- Test 1: Bank Loan Default ---")

    # 1. Grant Loan
    borrower = sim.firms[0]
    loan_amount = 1000.0

    # Simulate Loan Granting (Manual bypass of LoanMarket to isolate Bank logic)
    # Bank creates credit? Or uses reserves?
    # Bank.grant_loan just updates ledger. We need to handle the money.

    # Let's use Bank.grant_loan
    loan_id = sim.bank.grant_loan(borrower.id, loan_amount)

    # Manually simulate the Transfer (Credit Creation)
    # If Bank has enough reserves, it lends them.
    # sim.bank._sub_assets(loan_amount) # Reserve Drawdown
    # borrower._add_assets(loan_amount) # Borrower receives

    # Wait, if we use Transaction, TransactionProcessor handles it.
    # But here we want to test Bank.process_default.

    # Let's just inject the state of "Loan Exists" and "Money Exists"
    # Assume Loan was granted earlier and money is in the system.
    # We don't change M2 here (Money just moved).

    # Now simulate Default
    loan = sim.bank.loans[loan_id]

    m2_before_default = get_m2()
    logger.info(f"M2 Before Default: {m2_before_default}")

    # Trigger Default
    sim.bank.process_default(borrower, loan, sim.time)

    m2_after_default = get_m2()
    logger.info(f"M2 After Default: {m2_after_default}")

    drift_b = m2_after_default - m2_before_default
    logger.info(f"Drift B: {drift_b}")

    if drift_b == 0:
        logger.info("RESULT: M2 Unchanged. If money was created/lent, this means M2 is permanently expanded (Leak/Drift).")
        # If the loan principal was lost, Bank Equity should drop.
        # If Bank Assets (Reserves) didn't drop, then M2 didn't drop.
        # So the money lent out is still in circulation, but the matching Asset is gone.
        # This confirms Debt Shadow.

    # --- Test 2: Firm Liquidation & Reflux (Hypothesis C) ---
    logger.info("\n--- Test 2: Firm Liquidation Reflux ---")

    target_firm = sim.firms[1]
    target_firm.is_active = False # Mark for liquidation

    # Add some inventory
    target_firm.inventory['widget'] = 10.0
    # Add some capital
    target_firm.capital_stock = 500.0

    m2_before_liq = get_m2()
    logger.info(f"M2 Before Liquidation: {m2_before_liq}")

    # Run Lifecycle Manager
    sim.lifecycle_manager._handle_agent_liquidation(sim.world_state)

    m2_after_liq = get_m2()
    logger.info(f"M2 After Liquidation: {m2_after_liq}")

    drift_c = m2_after_liq - m2_before_liq
    logger.info(f"Drift C: {drift_c}")

    if drift_c > 0:
        logger.info(f"RESULT: M2 Increased by {drift_c}. Reflux Capture created money from inventory!")

    # --- Test 3: Tax Collection Reporting (Hypothesis A/Phantom) ---
    logger.info("\n--- Test 3: Liquidation Tax Reporting ---")
    # Check if Government stats updated
    # In Test 2, we liquidated a firm. If it had assets, tax should be collected/recorded.

    # Firm 1 had assets?
    # We didn't set assets explicitly, it had initial assets.
    # Let's check logs or just assume it had some.

    gov_revenue = sim.government.total_collected_tax
    logger.info(f"Government Total Tax Collected: {gov_revenue}")

    # If using correct `record_revenue`, this should be > 0 (if firm had assets)
    # If using broken `collect_tax`, this might be 0 (or low).

if __name__ == "__main__":
    reproduce_leaks()
