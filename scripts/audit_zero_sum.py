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
        f_assets = sum(f.get_financial_snapshot().get("total_assets", f.assets)
                       if hasattr(f, "get_financial_snapshot") else f.assets
                       for f in sim.firms)
        gov_assets = sim.government.assets

        # WO-106: Include Reflux Balance as it holds captured value before distribution
        reflux_balance = sim.reflux_system.balance if hasattr(sim, 'reflux_system') else 0.0

        return h_assets + f_assets + gov_assets + reflux_balance

    # Snapshot T0 state for detailed accounting
    # Use config default price if dynamic price is missing
    default_price = getattr(sim.config_module, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)

    def get_inventory_value_map(agents):
        val = 0.0
        for a in agents:
             # Firm inventory
             if hasattr(a, 'inventory'):
                 for item, qty in a.inventory.items():
                     price = a.last_prices.get(item, default_price) if hasattr(a, 'last_prices') else default_price
                     val += qty * price
             # Firm input inventory
             if hasattr(a, 'input_inventory'):
                 for item, qty in a.input_inventory.items():
                     # Inputs usually have same price as goods
                     val += qty * default_price
        return val

    def get_capital_stock(firms):
        return sum(f.capital_stock for f in firms)

    wealth_t0 = get_total_wealth(sim)
    inv_val_t0 = get_inventory_value_map(sim.firms) # Track input inventory specifically
    cap_stock_t0 = get_capital_stock(sim.firms)

    logger.info(f"Tick 0 Wealth: {wealth_t0:.2f} (Cap: {cap_stock_t0:.2f})")

    logger.info("Running Tick 1...")
    sim.run_tick()

    wealth_t1 = get_total_wealth(sim)
    cap_stock_t1 = get_capital_stock(sim.firms)

    logger.info(f"Tick 1 Wealth: {wealth_t1:.2f} (Cap: {cap_stock_t1:.2f})")

    diff = wealth_t1 - wealth_t0
    logger.info(f"Wealth Diff (T1 - T0): {diff:.2f}")

    # Detailed Flow Analysis
    # 1. Production Output Value (Gross)
    # Use exact price per firm specialization
    gross_production_value = 0.0
    for f in sim.firms:
        price = f.last_prices.get(f.specialization, default_price)
        gross_production_value += f.current_production * price

    # 2. Consumption (Value Destroyed)
    # Households don't expose 'consumed value' directly easily, but we know Consumption = Wealth Loss.
    # Firms consume Inputs.
    # We can infer Consumption + Input Usage by checking Inventory changes vs Production.
    # But simpler: We assume Unexplained Diff is Consumption + Depreciation.

    # 3. Depreciation (Capital Stock Loss)
    depreciation_loss = cap_stock_t0 - cap_stock_t1

    # 4. Input Consumption (Firm)
    # Hard to track exact input usage without snapshotting input_inventory.
    # Let's assume input_inventory change is mostly consumption.
    # But firms might buy inputs? (Trade). Trade is wealth transfer, not loss.
    # So Input Consumption = (Input_Inv_T0 - Input_Inv_T1) + Inputs_Bought.
    # If no trade (Tick 1 usually no trade?), then Delta Input Inv is Consumption.

    # 5. Household Consumption
    # sim.households[i].current_consumption (Value)
    household_consumption_value = sum(h.current_consumption for h in sim.households)

    # Predict Delta
    # Delta Wealth = Gross Production - HH Consumption - Depreciation - Input Consumption
    # If Input Consumption is not tracked, we might fail.
    # Let's see if Gross Production - HH Consumption - Depreciation aligns.

    predicted_diff = gross_production_value - household_consumption_value - depreciation_loss
    unexplained_diff = diff - predicted_diff

    logger.info(f"Analysis: GrossProd={gross_production_value:.2f}, HH_Cons={household_consumption_value:.2f}, Depr={depreciation_loss:.2f}")
    logger.info(f"Predicted Delta (Prod - Cons - Depr): {predicted_diff:.2f}")
    logger.info(f"Actual Delta: {diff:.2f}")
    logger.info(f"Unexplained Variance (Inputs?): {unexplained_diff:.2f}")

    # PR Review: Tolerance tightened to 0.1%
    tolerance = 0.001 # 0.1%

    # We accept Variance if it likely Input Consumption (Negative Unexplained).
    # If Unexplained is Negative, it means we predicted MORE wealth than actual -> Something consumed it.
    # Input Consumption is the missing sink.
    # If Unexplained is Positive, we have Created Money from nowhere. That is BAD.

    # We enforce STRICT no-creation (Positive Unexplained <= tolerance).
    # We allow Sinks (Negative Unexplained) to be larger IF we attribute it to inputs.
    # But the user asked for "Tolerance 0.1%".
    # I should assume "Net Change" should be explained.

    if abs(unexplained_diff) > wealth_t0 * tolerance:
         # If variance is negative, check if it fits Input Consumption profile?
         # For now, log error but provide context.
         logger.error(f"FAILED: Initial Sink detected! (>0.1% unexplained variance). Unexplained: {unexplained_diff:.2f}")
    else:
         logger.info("PASSED: Initial Sink check (Unexplained variance < 0.1%).")

    # PR Review: Tolerance tightened to 0.1%
    tolerance = 0.001 # 0.1%

    # We check if unexplained variance is within tolerance
    if abs(unexplained_diff) > wealth_t0 * tolerance:
         logger.error(f"FAILED: Initial Sink detected! (>0.1% unexplained variance). Unexplained: {unexplained_diff:.2f}")
         # Also fail if the raw diff is huge and we can't explain it, but here we try to explain it.
    else:
         logger.info("PASSED: Initial Sink check (Unexplained variance < 0.1%).")

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
