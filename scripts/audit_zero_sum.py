import sys
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from simulation.firms import Firm
from simulation.dtos.api import SimulationState
from modules.system.api import DEFAULT_CURRENCY

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
        # Handle dict assets from EconStateDTO
        h_assets = 0.0
        for h in sim.households:
             assets = h._econ_state.assets
             if isinstance(assets, dict):
                 h_assets += assets.get(DEFAULT_CURRENCY, 0.0)
             else:
                 h_assets += float(assets)

        f_assets = sum(f.get_financial_snapshot().get("total_assets", f.assets)
                       if hasattr(f, "get_financial_snapshot") else f.assets
                       for f in sim.firms)
        gov_assets = sim.government.assets

        return h_assets + f_assets + gov_assets

    # Snapshot T0 state for detailed accounting
    # Use config default price if dynamic price is missing
    default_price = getattr(sim.config_module, "GOODS_INITIAL_PRICE", {}).get("default", 10.0)

    def get_inventory_value_map(agents):
        val = 0.0
        for a in agents:
             # Firm inventory
             if hasattr(a, 'inventory'):
                 # Check if inventory is dict or manager
                 inventory = a.inventory
                 if hasattr(inventory, 'get_all_items'): # IInventoryHandler
                     inventory = inventory.get_all_items()

                 for item, qty in inventory.items():
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
    household_consumption_value = sum(h._econ_state.current_consumption for h in sim.households)

    # 3. Depreciation (Capital Stock Loss)
    depreciation_loss = cap_stock_t0 - cap_stock_t1

    predicted_diff = gross_production_value - household_consumption_value - depreciation_loss
    unexplained_diff = diff - predicted_diff

    logger.info(f"Analysis: GrossProd={gross_production_value:.2f}, HH_Cons={household_consumption_value:.2f}, Depr={depreciation_loss:.2f}")
    logger.info(f"Predicted Delta (Prod - Cons - Depr): {predicted_diff:.2f}")
    logger.info(f"Actual Delta: {diff:.2f}")
    logger.info(f"Unexplained Variance (Inputs?): {unexplained_diff:.2f}")

    # PR Review: Tolerance tightened to 0.1%
    tolerance = 0.001 # 0.1%

    if abs(unexplained_diff) > wealth_t0 * tolerance:
         logger.error(f"FAILED: Initial Sink detected! (>0.1% unexplained variance). Unexplained: {unexplained_diff:.2f}")
    else:
         logger.info("PASSED: Initial Sink check (Unexplained variance < 0.1%).")

    # 2. Check Central Bank Fiat (QE)
    # ------------------------------------------------------------------
    logger.info("Checking Central Bank Fiat Authority...")
    cb = sim.central_bank
    # Use withdraw directly, wallet allows negative
    try:
        cb.withdraw(1000.0)
        logger.info(f"PASSED: CB Withdraw (Fiat) successful.")
    except Exception as e:
        logger.error(f"FAILED: CB Withdraw raised {e}")

    # 3. Check Immigration Funding
    # ------------------------------------------------------------------
    logger.info("Checking Immigration Funding...")
    gov = sim.government
    # Gov assets
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

    # 4. Check Liquidation Escheatment (Government Capture)
    # ------------------------------------------------------------------
    logger.info("Checking Liquidation Escheatment (to Government)...")
    # Create victim firm (orphan, no shareholders)
    victim = sim.firms[0]
    # Inject via IInventoryHandler if possible, or hack if needed for test
    if hasattr(victim, 'inventory') and hasattr(victim.inventory, 'add_item'):
        victim.inventory.add_item('basic_food', 10.0)
    else:
        # Fallback for old structure if applicable, but we are new
        pass

    victim.capital_stock = 500.0
    victim.finance_state.total_shares = 1000.0
    victim.finance_state.treasury_shares = 1000.0 # 100% Treasury

    # Ensure it has cash
    victim_cash = 1000.0
    if hasattr(victim, 'deposit'):
         victim.deposit(victim_cash)
         # If existing assets > victim_cash, withdraw difference?
         # Or just add. We check delta.

    # Store pre-liquidation assets to verify capture
    pre_liq_assets = victim.assets

    victim.is_active = False # Mark for death

    initial_gov = sim.government.assets

    # Create SimulationState DTO for lifecycle manager
    sim_state = SimulationState(
        time=sim.time,
        households=sim.households,
        firms=sim.firms,
        agents=sim.agents,
        markets=sim.markets,
        government=sim.government,
        bank=sim.bank,
        central_bank=sim.central_bank,
        escrow_agent=None,
        stock_market=sim.stock_market,
        stock_tracker=sim.stock_tracker if hasattr(sim, 'stock_tracker') else None,
        goods_data=sim.goods_data,
        market_data={},
        config_module=sim.config_module,
        tracker=sim.tracker,
        logger=sim.logger,
        ai_training_manager=sim.ai_training_manager,
        ai_trainer=sim.ai_trainer,
        next_agent_id=sim.next_agent_id,
        real_estate_units=sim.real_estate_units,
        settlement_system=sim.world_state.settlement_system,
        shareholder_registry=sim.shareholder_registry if hasattr(sim, 'shareholder_registry') else None
    )

    # Run lifecycle manager
    sim.lifecycle_manager._handle_agent_liquidation(sim_state)

    final_gov = sim.government.assets
    captured = final_gov - initial_gov
    logger.info(f"Gov Assets Before: {initial_gov:.2f} | After: {final_gov:.2f} | Captured: {captured:.2f}")

    # We expect Government to capture the Cash.
    if abs(captured - pre_liq_assets) < 1.0:
        logger.info(f"PASSED: Government captured liquidation cash.")
    else:
        logger.error(f"FAILED: Government capture mismatch. Expected ~{pre_liq_assets}, got {captured}")

if __name__ == "__main__":
    audit_integrity()
