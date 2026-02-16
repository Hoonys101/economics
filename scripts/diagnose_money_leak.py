
import sys
import os
import logging
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from modules.common.utils.logging_manager import setup_logging
import config
from modules.system.api import DEFAULT_CURRENCY

def diagnose():
    setup_logging()

    # 1. Suppress Engine Noise
    # Set root logger to ERROR to silence DEBUG/INFO/WARNING from the engine
    logging.getLogger().setLevel(logging.ERROR)

    # 2. Configure DIAGNOSE Logger
    logger = logging.getLogger("DIAGNOSE")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent propagation to root logger

    # Clean output handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    # Reset handlers to ensure clean state
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

    # 3. Simulation Initialization
    config.TICKS_PER_YEAR = 100
    sim = create_simulation()
    
    def get_balances():
        # Use WorldState M2 calculation (pennies as float)
        total_pennies_float = sim.world_state.get_total_system_money_for_diagnostics(DEFAULT_CURRENCY)
        
        # Breakdown for logging (optional, using float for display)
        h_sum = sum(h.balance_pennies for h in sim.households if h._bio_state.is_active)
        
        # Monetary Policy Tracking
        issued = 0.0
        destroyed = 0.0
        if hasattr(sim.government, "monetary_ledger"):
             issued = sim.government.monetary_ledger.total_money_issued.get(DEFAULT_CURRENCY, 0.0)
             destroyed = sim.government.monetary_ledger.total_money_destroyed.get(DEFAULT_CURRENCY, 0.0)

        return {
            "total_pennies": total_pennies_float,
            "total": total_pennies_float / 100.0, # Convert to dollars for display
            "h_active": float(h_sum) / 100.0,
            "issued": issued / 100.0, # Ledger tracks pennies (from tx.price)
            "destroyed": destroyed / 100.0
        }

    last_b = get_balances()
    logger.info(f"START | Total: {last_b['total']:,.2f}")

    max_abs_leak = 0.0

    for tick in range(1, 101): # Run for 100 ticks (reduced for speed)
        sim.run_tick()
        curr_b = get_balances()

        # Calculate Delta in Total Assets (Dollars)
        diff = curr_b['total'] - last_b['total']
        
        # Calculate Authorized Monetary Delta (Dollars)
        # Ledger tracks in face value (dollars if not specified otherwise, but we should assume dollars based on float usage)
        monetary_delta = (curr_b['issued'] - last_b['issued']) - (curr_b['destroyed'] - last_b['destroyed'])

        # Leak = Unexplained Change
        leak = diff - monetary_delta
        
        # Update Max Leak
        if abs(leak) > max_abs_leak:
            max_abs_leak = abs(leak)
        
        # Structured Output
        logger.info(f"TICK: {tick:3} | LEAK: {leak:10.4f} | TOTAL: {curr_b['total']:15,.2f} | DELTA: {diff:10.4f} | AUTH: {monetary_delta:10.4f}")
        
        # Forensic Mode
        if abs(leak) > 1.0:
            logger.info(f"  [FORENSIC] Significant Leak Detected at Tick {tick}")
            logger.info(f"  Reconciliation Check:")
            logger.info(f"    - System Asset Delta:    {diff:15,.4f}")
            logger.info(f"    - Money Supply Delta:    {monetary_delta:15,.4f}")
            logger.info(f"    - Unexplained (Leak):    {leak:15,.4f}")

        last_b = curr_b

    # Final Verdict
    print("-" * 50)
    logger.info(f"MAX LEAK: {max_abs_leak:.4f}")
    if max_abs_leak > 1.0:
        logger.info("[FAIL] Significant Leak Detected")
    else:
        logger.info("[SUCCESS] No Significant Leak")

if __name__ == "__main__":
    diagnose()
