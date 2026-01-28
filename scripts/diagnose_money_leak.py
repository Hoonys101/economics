
import sys
import os
import logging
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from utils.logging_manager import setup_logging
import config

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
        h_sum = sum(h.assets for h in sim.households if h.is_active)
        f_sum = sum(f.assets for f in sim.firms if f.is_active)
        # 소멸 과정에 있는 에이전트 포함 (Ghost check)
        h_inactive = sum(h.assets for h in sim.households if not h.is_active)
        f_inactive = sum(f.assets for f in sim.firms if not f.is_active)
        
        gov = sim.government.assets
        bank = sim.bank.assets
        
        # M2 통계
        total = h_sum + f_sum + gov + bank + h_inactive + f_inactive
        return {
            "total": total,
            "h_active": h_sum,
            "f_active": f_sum,
            "h_ghost": h_inactive,
            "f_ghost": f_inactive,
            "gov": gov,
            "bank": bank,
            "issued": getattr(sim.government, "total_money_issued", 0.0),
            "destroyed": getattr(sim.government, "total_money_destroyed", 0.0)
        }

    last_b = get_balances()
    logger.info(f"START | Total: {last_b['total']:,.2f} | H: {last_b['h_active']:,.2f} | Bank: {last_b['bank']:,.2f}")

    max_abs_leak = 0.0

    for tick in range(1, 501): # Run for 500 ticks
        sim.run_tick()
        curr_b = get_balances()
        diff = curr_b['total'] - last_b['total']
        
        # 발행/파괴 보정
        monetary_delta = (curr_b['issued'] - last_b['issued']) - (curr_b['destroyed'] - last_b['destroyed'])
        leak = diff - monetary_delta
        
        # Update Max Leak
        if abs(leak) > max_abs_leak:
            max_abs_leak = abs(leak)
        
        # Structured Output
        logger.info(f"TICK: {tick:3} | LEAK: {leak:10.4f} | TOTAL_M2: {curr_b['total']:15,.2f}")
        
        # Forensic Mode
        if abs(leak) > 1.0:
            logger.info(f"  [FORENSIC] Significant Leak Detected at Tick {tick}")
            logger.info(f"  Reconciliation Check:")
            logger.info(f"    - System Asset Delta:    {diff:15,.4f}")
            logger.info(f"    - Money Supply Delta:    {monetary_delta:15,.4f}")
            logger.info(f"    - Unexplained (Leak):    {leak:15,.4f}")

            # Transaction Summary
            tx_summary = defaultdict(lambda: {'count': 0, 'volume': 0.0})

            # sim.transactions should hold the transactions of the current tick
            current_transactions = getattr(sim, 'transactions', [])

            for tx in current_transactions:
                t_type = tx.transaction_type
                # Group generic/other types by item_id if needed
                if t_type == 'other' or t_type is None:
                    t_type = f"other:{tx.item_id}"

                vol = tx.price * tx.quantity
                tx_summary[t_type]['count'] += 1
                tx_summary[t_type]['volume'] += vol

            logger.info(f"  Transaction Summary:")
            logger.info(f"    {'Type':<25} | {'Count':>8} | {'Volume':>15}")
            logger.info(f"    {'-'*25}-+-{'-'*8}-+-{'-'*15}")

            for t_type, stats in sorted(tx_summary.items()):
                logger.info(f"    {t_type:<25} | {stats['count']:8d} | {stats['volume']:15,.2f}")
            logger.info("")

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
