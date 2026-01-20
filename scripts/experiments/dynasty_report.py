"""
Dynasty Report (Phase Alpha Optimizer)
Goal: Run 1000 ticks simulation with maximized speed and report TPS.
"""
import sys
import os
import time
import logging
import argparse

# Add project root to path
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Log Suppression (Task B)
logging.getLogger("simulation").setLevel(logging.WARNING)
logging.getLogger("simulation.engine").setLevel(logging.WARNING)
# Also suppress root to be sure, but allow our script to log
logging.getLogger().setLevel(logging.WARNING)

import config
from main import create_simulation

# Custom Logger for Report
report_logger = logging.getLogger("DYNASTY_REPORT")
report_logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(message)s'))
report_logger.addHandler(handler)
report_logger.propagate = False

def run_dynasty_test(ticks: int = 1000):
    report_logger.info(f"🏎️ Starting Dynasty Speed Test: {ticks} Ticks")

    start_time = time.time()

    # Initialize
    # We use overrides to match Iron Test setup for stability
    overrides = {
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 5000.0,
        "INITIAL_FIRM_CAPITAL_MEAN": 50000.0,
        "BATCH_SAVE_INTERVAL": 50 # Reinforce config level too
    }

    simulation = create_simulation(overrides=overrides)
    init_time = time.time()
    report_logger.info(f"Initialization took: {init_time - start_time:.4f}s")

    # Run Loop
    try:
        for t in range(1, ticks + 1):
            simulation.run_tick()

            if t % 100 == 0:
                elapsed = time.time() - init_time
                current_tps = t / elapsed if elapsed > 0 else 0
                report_logger.info(f"Tick {t} complete. Avg TPS: {current_tps:.1f}")

    except Exception as e:
        report_logger.error(f"Simulation Crashed: {e}")
        import traceback
        traceback.print_exc()

    end_time = time.time()
    total_time = end_time - init_time
    total_tps = ticks / total_time if total_time > 0 else 0

    report_logger.info(f"\n✅ Simulation Complete")
    report_logger.info(f"Total Time (Loop): {total_time:.4f}s")
    report_logger.info(f"Total TPS: {total_tps:.2f}")

    if total_tps > 0:
        minutes = total_time / 60.0
        report_logger.info(f"Est. 1000 Ticks Time: {minutes:.2f} minutes")

    simulation.finalize_simulation()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=1000)
    args = parser.parse_args()

    run_dynasty_test(args.ticks)
