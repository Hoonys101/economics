import sys
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from simulation.firms import Firm

def audit_integrity():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("AUDIT")

    logger.info("Initializing Simulation via main.create_simulation...")

    # Use standard config with minimal overrides
    overrides = {
        "NUM_HOUSEHOLDS": 50,
        "NUM_FIRMS": 10,
        "INITIAL_GOVERNMENT_ASSETS": 10000.0,
        "INITIAL_BANK_ASSETS": 50000.0
    }
    sim = create_simulation(overrides)

    # 1. Check Initial Sink (Tick 0 vs Tick 1)
    # ------------------------------------------------------------------

    def get_total_wealth(sim):
        h_assets = sum(h.assets for h in sim.households)
        # Firm Assets should include Capital + Inventory
        # Using the same logic we added to EconomicIndicatorTracker (via get_financial_snapshot)
        f_assets = sum(f.get_financial_snapshot().get("total_assets", f.assets)
                       if hasattr(f, "get_financial_snapshot") else f.assets
                       for f in sim.firms)
        gov_assets = sim.government.assets
        # CB assets
        # Focus on Agents holding wealth
        return h_assets + f_assets + gov_assets

    wealth_t0 = get_total_wealth(sim)
    logger.info(f"Tick 0 Wealth: {wealth_t0:.2f}")

    logger.info("Running Tick 1...")
    sim.run_tick()

    wealth_t1 = get_total_wealth(sim)
    logger.info(f"Tick 1 Wealth: {wealth_t1:.2f}")

    diff = wealth_t1 - wealth_t0
    logger.info(f"Wealth Diff (T1 - T0): {diff:.2f}")

    if abs(diff) > wealth_t0 * 0.2: # Allow 20% variance
         logger.error("FAILED: Huge Wealth Sink detected! (>20% loss)")
    else:
         logger.info("PASSED: Initial Sink check.")

    # 2. Check Central Bank Fiat (QE)
    # ------------------------------------------------------------------
    logger.info("Checking Central Bank Fiat Authority...")
    cb = sim.central_bank
    cb.assets['cash'] = 0.0
    try:
        cb.withdraw(1000.0)
        logger.info(f"PASSED: CB Withdraw (Fiat) successful. Balance: {cb.assets['cash']}")
    except Exception as e:
        logger.error(f"FAILED: CB Withdraw raised {e}")

    # 3. Check Immigration Funding
    # ------------------------------------------------------------------
    logger.info("Checking Immigration Funding...")
    gov = sim.government
    gov.assets = 10000.0
    initial_gov = gov.assets

    # We call _create_immigrants directly to force it
    logger.info(f"Gov Assets Before: {initial_gov}")
    immigrants = sim.immigration_manager._create_immigrants(sim, 1)

    if immigrants:
        # Check if Government paid
        paid_amount = initial_gov - gov.assets
        logger.info(f"Gov Assets After: {gov.assets} (Paid: {paid_amount})")

        if paid_amount > 2000.0: # Expecting 3000-5000
            logger.info(f"PASSED: Immigration funded by Govt.")
        else:
            logger.error(f"FAILED: Government did not pay enough. Paid: {paid_amount}")
    else:
        logger.warning("No immigrants created (unexpected)")

    # 4. Check Reflux Capture (Liquidation)
    # ------------------------------------------------------------------
    logger.info("Checking Reflux System Capture...")
    # Create a dummy firm to kill or use existing
    victim = sim.firms[0]
    victim.inventory['basic_food'] = 10.0
    victim.capital_stock = 500.0
    victim.assets = 100.0

    # Ensure market exists for basic_food for pricing
    if 'basic_food' not in sim.markets:
         sim.markets['basic_food'] = type('MockMarket', (), {'avg_price': 10.0, 'current_price': 10.0})()

    victim.is_active = False # Mark for death

    initial_reflux = sim.reflux_system.balance
    logger.info(f"Reflux Balance Before: {initial_reflux}")

    # Run lifecycle manager
    sim.lifecycle_manager._handle_agent_liquidation(sim)

    final_reflux = sim.reflux_system.balance
    captured = final_reflux - initial_reflux
    logger.info(f"Reflux Balance After: {final_reflux} (Captured: {captured})")

    if captured > 0:
        logger.info(f"PASSED: Reflux System captured liquidation value.")
    else:
        logger.error("FAILED: Reflux System captured nothing.")

if __name__ == "__main__":
    audit_integrity()
