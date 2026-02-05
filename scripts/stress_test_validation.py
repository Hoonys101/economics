import sys
import os
import argparse
import logging
from typing import Dict, Any, List, Optional

# Add current directory to path
sys.path.append(os.getcwd())

from main import create_simulation
from modules.system.api import DEFAULT_CURRENCY

def run_validation(ticks: int, scenario: str):
    print(f"--- PHASE 6 STRESS TEST VALIDATION START ({ticks} Ticks, Scenario: {scenario}) ---")
    
    # Configure scenario via config manager before creation if needed
    # But initializer.py reads "simulation.active_scenario"
    os.environ["SIMULATION_ACTIVE_SCENARIO"] = scenario
    
    sim = create_simulation()
    state = sim.world_state
    
    # Established baseline at initialization
    baseline_money = state.baseline_money_supply
    print(f"Initial Baseline Money (M2): {baseline_money:,.2f}")

    total_leak = 0.0
    
    for t in range(1, ticks + 1):
        pre_money = state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)
        
        # Capture Authorized Delta (Cumulative) before the tick
        pre_auth_delta = sim.government.get_monetary_delta(DEFAULT_CURRENCY)
        
        # Run the tick
        sim.run_tick()
        
        post_money = state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0)
        post_auth_delta = sim.government.get_monetary_delta(DEFAULT_CURRENCY)
        
        tick_delta = post_money - pre_money
        tick_auth_delta = post_auth_delta - pre_auth_delta
        
        # Check for intermediate leaks in transaction processor if possible
        # But here we check end-of-tick integrity
        
        tick_leak = tick_delta - tick_auth_delta
        total_leak += tick_leak
        
        if abs(tick_leak) > 0.0001:
            print(f"⚠️ LEAK DETECTED at Tick {t}: {tick_leak:,.4f} | M2: {post_money:,.2f}")
        
        if t % 10 == 0 or t == 1:
            indicators = sim.tracker.get_latest_indicators()
            gdp = indicators.get("gdp", 0.0)
            unempl = indicators.get("unemployment_rate", 0.0)
            print(f"Tick {t:3}: M2={post_money:10,.2f} | Leak={tick_leak:10.4f} | GDP={gdp:10,.2f} | Unempl={unempl:5.1f}%")

    print("\n" + "="*50)
    print(f"VERIFICATION COMPLETE")
    print(f"Total Ticks: {ticks}")
    print(f"Final M2: {state.calculate_total_money().get(DEFAULT_CURRENCY, 0.0):,.2f}")
    print(f"Cumulative Leak: {total_leak:,.6f}")
    print("="*50)

    if abs(total_leak) > 0.01:
        print("❌ FAILED: Significant monetary leak detected.")
        sys.exit(1)
    else:
        print("✅ PASSED: Monetary integrity maintained (0.0000 leak).")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 6 Stress Test Validation")
    parser.add_argument("--ticks", type=int, default=100, help="Number of ticks to run")
    parser.add_argument("--scenario", type=str, default="phase29_depression", help="Scenario name")
    args = parser.parse_args()
    
    run_validation(args.ticks, args.scenario)
