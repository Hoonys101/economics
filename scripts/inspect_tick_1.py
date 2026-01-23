
import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
import config

def inspect_tick_1():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("INSPECT")
    
    sim = create_simulation()
    
    def get_state():
        h_active = sum(h.assets for h in sim.households if h.is_active)
        f_active = sum(f.assets for f in sim.firms if f.is_active)
        gov = sim.government.assets
        bank = sim.bank.assets
        reflux = sim.reflux_system.balance if hasattr(sim, 'reflux_system') else 0.0
        write_offs = sim.bank.total_write_offs if hasattr(sim.bank, 'total_write_offs') else 0.0
        cb_cash = sim.central_bank.assets.get('cash', 0.0) if hasattr(sim, 'central_bank') and hasattr(sim.central_bank, 'assets') else 0.0
        issued = getattr(sim.government, "total_money_issued", 0.0)
        destroyed = getattr(sim.government, "total_money_destroyed", 0.0)
        
        total = h_active + f_active + gov + bank + reflux + write_offs + cb_cash
        return {
            "total": total,
            "h": h_active,
            "f": f_active,
            "gov": gov,
            "bank": bank,
            "reflux": reflux,
            "write_offs": write_offs,
            "cb_cash": cb_cash,
            "net_monetary": issued - destroyed
        }

    before = get_state()
    logger.info(f"BEFORE | Total: {before['total']:.2f} | H: {before['h']:.2f} | F: {before['f']:.2f} | Gov: {before['gov']:.2f} | Bank: {before['bank']:.2f}")

    sim.run_tick()
    
    after = get_state()
    logger.info(f"AFTER  | Total: {after['total']:.2f} | H: {after['h']:.2f} | F: {after['f']:.2f} | Gov: {after['gov']:.2f} | Bank: {after['bank']:.2f}")
    
    drift = after['total'] - before['total']
    monetary_change = after['net_monetary'] - before['net_monetary']
    leak = drift - monetary_change
    
    logger.info(f"DIFF   | Drift: {drift:+.2f} | Monetary: {monetary_change:+.2f} | LEAK: {leak:+.4f}")
    
    # Check transactions
    logger.info(f"PROCESSED TRANSACTIONS: {len(sim.world_state.transactions)}")
    for tx in sim.world_state.transactions:
         logger.info(f"  TX: {tx.transaction_type} | {tx.buyer_id} -> {tx.seller_id} | Amt: {tx.price:.2f}")

if __name__ == "__main__":
    inspect_tick_1()
