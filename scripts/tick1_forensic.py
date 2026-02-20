
import sys
import logging
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from modules.common.utils.logging_manager import setup_logging
import config

def forensic_tick1():
    setup_logging()
    # Suppress noise
    logging.getLogger().setLevel(logging.ERROR)
    
    logger = logging.getLogger("FORENSIC")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.propagate = False

    # Initialize Simulation
    sim = create_simulation()
    
    def get_system_snapshot():
        # Using .total_wealth which returns int pennies
        h_sum = sum(h.total_wealth for h in sim.world_state.households if h.is_active)
        f_sum = sum(f.total_wealth for f in sim.world_state.firms if f.is_active)
        
        # Government is a singleton in WorldState
        gov_sum = sim.world_state.government.total_wealth if sim.world_state.government else 0
        
        bank_wealth = sim.world_state.bank.total_wealth if sim.world_state.bank else 0
        
        # M2 = Sum(Cash) - Bank Reserves + Bank Deposits
        # For simplicity in leak detection, we look at the total sum of all wallets/assets
        # since money should only move between them (closed system).
        total_wallets = h_sum + f_sum + gov_sum + bank_wealth
        
        return {
            "total_wallets": total_wallets,
            "h": h_sum,
            "f": f_sum,
            "gov": gov_sum,
            "bank": bank_wealth
        }

    # --- TICK 0 ---
    snap0 = get_system_snapshot()
    logger.info("=== TICK 0 SNAPSHOT ===")
    logger.info(f"Total Assets: {snap0['total_wallets']:,}")
    logger.info(f"  Households: {snap0['h']:,}")
    logger.info(f"  Firms:      {snap0['f']:,}")
    logger.info(f"  Gov:        {snap0['gov']:,}")
    logger.info(f"  Bank:       {snap0['bank']:,}")
    
    # --- RUN TICK 1 ---
    sim.run_tick()
    
    # --- TICK 1 ---
    snap1 = get_system_snapshot()
    diff = snap1['total_wallets'] - snap0['total_wallets']
    
    logger.info("\n=== TICK 1 SNAPSHOT ===")
    logger.info(f"Total Assets: {snap1['total_wallets']:,}")
    logger.info(f"  Households: {snap1['h']:,}")
    logger.info(f"  Firms:      {snap1['f']:,}")
    logger.info(f"  Gov:        {snap1['gov']:,}")
    logger.info(f"  Bank:       {snap1['bank']:,}")
    
    logger.info(f"\nNET CHANGE (LEAK): {diff:,}")
    
    # --- TRANSACTION ANALYSIS ---
    logger.info("\n=== TICK 1 TRANSACTIONS ===")
    tx_summary = defaultdict(lambda: {'count': 0, 'volume': 0})
    
    # Access transactions from WorldState
    transactions = sim.world_state.transactions
    for tx in transactions:
        t_type = tx.transaction_type or "unknown"
        vol = int(tx.price * tx.quantity)
        tx_summary[t_type]['count'] += 1
        tx_summary[t_type]['volume'] += vol
        
    logger.info(f"{'Type':<20} | {'Count':>8} | {'Volume':>15}")
    logger.info("-" * 47)
    for t_type, stats in tx_summary.items():
        logger.info(f"{t_type:<20} | {stats['count']:8d} | {stats['volume']:15,}")

    # Check for direct money creation/destruction outside transactions
    # (e.g. initial endowments in tick 1?)

if __name__ == "__main__":
    forensic_tick1()
