
import sys
import os
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from utils.logging_manager import setup_logging
import config

def diagnose():
    setup_logging()
    logger = logging.getLogger("DIAGNOSE")
    
    # 1. 시뮬레이션 초기화
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
        reflux = sim.reflux_system.balance if hasattr(sim, 'reflux_system') else 0.0
        # New Buckets from Jules hunt
        write_offs = sim.bank.total_write_offs if hasattr(sim.bank, 'total_write_offs') else 0.0
        cb_cash = sim.central_bank.assets.get('cash', 0.0) if hasattr(sim, 'central_bank') and hasattr(sim.central_bank, 'assets') else 0.0
        
        # M2 통계
        total = h_sum + f_sum + gov + bank + reflux + h_inactive + f_inactive + write_offs + cb_cash
        return {
            "total": total,
            "h_active": h_sum,
            "f_active": f_sum,
            "h_ghost": h_inactive,
            "f_ghost": f_inactive,
            "gov": gov,
            "bank": bank,
            "reflux": reflux,
            "write_offs": write_offs,
            "cb_cash": cb_cash,
            "issued": getattr(sim.government, "total_money_issued", 0.0),
            "destroyed": getattr(sim.government, "total_money_destroyed", 0.0)
        }

    last_b = get_balances()
    logger.info(f"START | Total: {last_b['total']:,.2f} | H: {last_b['h_active']:,.2f} | Bank: {last_b['bank']:,.2f}")

    for tick in range(1, 11): # 초기 10틱만 집중 관찰
        sim.run_tick()
        curr_b = get_balances()
        diff = curr_b['total'] - last_b['total']
        
        # 발행/파괴 보정
        monetary_delta = (curr_b['issued'] - last_b['issued']) - (curr_b['destroyed'] - last_b['destroyed'])
        leak = diff - monetary_delta
        
        logger.info(f"TICK {tick:2} | Total: {curr_b['total']:,.2f} | Diff: {diff:+.2f} | Leak: {leak:+.4f}")
        
        if abs(leak) > 0.01:
            logger.error(f"!!! LEAK DETECTED at Tick {tick} !!!")
            # 세부 내역 비교
            for key in curr_b:
                change = curr_b[key] - last_b[key]
                if abs(change) > 0:
                    logger.info(f"  - {key:8}: {curr_b[key]:12,.2f} ({change:+.2f})")
        
        last_b = curr_b

if __name__ == "__main__":
    diagnose()
