import sys
import os
import logging
from typing import TYPE_CHECKING

# Add root directory to python path
sys.path.append(os.getcwd())

from main import create_simulation

def verify_td_111():
    print("--- VERIFY TD-111 START ---")
    sim = create_simulation()

    # Run a few ticks to generate some economic activity
    print("Running simulation for 10 ticks...")
    for i in range(10):
        sim.run_tick()

    world_state = sim.world_state
    tracker = world_state.tracker

    # Fetch values
    ws_total = world_state.calculate_total_money()
    m2_total = tracker.get_m2_money_supply(world_state)

    cb_balance = world_state.central_bank.assets.get('cash', 0.0) if world_state.central_bank else 0.0

    print(f"WorldState Total Money (Integrity): {ws_total:,.6f}")
    print(f"M2 Money Supply (Reporting): {m2_total:,.6f}")
    print(f"Central Bank Cash: {cb_balance:,.6f}")

    # Calculate sum
    calculated_total = m2_total + cb_balance

    diff = abs(ws_total - calculated_total)
    print(f"Difference: {diff:,.10f}")

    # Assert correctness
    assert diff < 1e-6, f"Integrity check failed! Diff: {diff}"

    print("✅ TD-111 Integrity Check Passed.")

    # Verify that M2 from tracker (via run_tick) matches get_m2_money_supply
    # We need to access the latest tracked value.
    latest_metrics = tracker.get_latest_indicators()
    tracked_m2 = latest_metrics.get("money_supply", -1.0)
    print(f"Tracked M2 (from metrics): {tracked_m2:,.6f}")

    if abs(tracked_m2 - m2_total) < 1e-6:
         print("✅ Tracked M2 matches calculated M2.")
    elif abs(tracked_m2 - ws_total) < 1e-6:
         print("❌ Tracked M2 matches Total Money. (Code is likely NOT YET modified)")
    else:
         print(f"⚠️ Tracked M2 ({tracked_m2}) matches neither M2 ({m2_total}) nor Total ({ws_total}).")

if __name__ == "__main__":
    verify_td_111()
