from main import create_simulation
import logging
import sys

def verify_phase23():
    print("--- VERIFY PHASE 23: INDUSTRIAL REVOLUTION ---")

    # 1. Setup Simulation with Scenario Override
    # Note: ConfigManager uses dot notation, but legacy config might need underscore.
    # main.py does: if overrides: for key, value in overrides.items(): setattr(config, key, value)
    # So we should pass the legacy key style: SIMULATION_ACTIVE_SCENARIO
    overrides = {
        "SIMULATION_ACTIVE_SCENARIO": "phase23_industrial_rev",
        "SIMULATION_TICKS": 150, # Enough to see effect
        "INITIAL_FIRM_CAPITAL_MEAN": 500000.0, # Give firms more runway
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 50000.0, # Give households buying power
        "MAX_CONSECUTIVE_LOSS_TURNS": 50, # Prevent early bankruptcy
        # Force competition in basic_food
        "FIRM_SPECIALIZATIONS": {
            0: "basic_food", 1: "basic_food", 2: "basic_food", 3: "basic_food", 4: "basic_food",
            5: "clothing", 6: "clothing",
            7: "luxury_food", 8: "luxury_food",
            9: "education_service"
        }
    }

    # Disable logs to keep output clean, except for our print statements
    logging.getLogger().setLevel(logging.ERROR)

    sim = create_simulation(overrides=overrides)

    print(f"Scenario loaded: {getattr(sim.config_module, 'SIMULATION_ACTIVE_SCENARIO', 'Unknown')}")
    # Verify parameter injection
    print(f"Tech Multiplier: {getattr(sim.config_module, 'TECH_FERTILIZER_MULTIPLIER', 'Not Set')}")

    metrics = {
        "ticks": [],
        "supply": [],
        "demand": [],
        "price": [],
        "population": []
    }

    intro_tick = -1
    crash_tick = -1
    start_price = 0.0
    peak_ratio = 0.0

    # We need to run enough ticks to trigger the event and see effects
    # Unlock is at Tick 50.

    for tick in range(overrides["SIMULATION_TICKS"]):
        # Phase_Production is handled within run_tick via TickOrchestrator
        sim.run_tick()

        # Collect Data
        market = sim.markets["basic_food"]
        # Use recorded stats from pre-clear (since we are post-run_tick)
        supply = getattr(market, "last_tick_supply", market.get_total_supply())
        demand = getattr(market, "last_tick_demand", market.get_total_demand())
        price = market.get_daily_avg_price()
        population = len([h for h in sim.households if h.is_active])

        # Log periodically
        if tick % 10 == 0:
            print(f"Tick {tick}: Pop={population}, Price={price:.2f}, S/D={supply:.1f}/{demand:.1f}")

        metrics["ticks"].append(tick)
        metrics["supply"].append(supply)
        metrics["demand"].append(demand)
        metrics["price"].append(price)
        metrics["population"].append(population)

        ratio = supply / demand if demand > 0 else 0
        if ratio > peak_ratio:
            peak_ratio = ratio

        # Detect Introduction (when tech is unlocked or multiplier effective?)
        # Unlock tick is 50.
        if tick == 50:
            intro_tick = tick
            start_price = price
            print(f"--- Fertilizer Intro at Tick {tick}, Price: {price:.2f} ---")

        # Detect Price Crash
        if intro_tick > 0 and crash_tick == -1:
            # We look for a drop from the price AT intro
            if start_price > 0 and price <= start_price * 0.5:
                crash_tick = tick
                print(f"!!! Price Crash detected at Tick {tick} ({price:.2f} <= {start_price * 0.5:.2f}) !!!")

        # Stop early if population cap reached
        if population >= 2000:
            print("Population limit reached.")
            break

    # Analysis
    print("\n--- RESULTS ---")
    print(f"Fertilizer Intro: Tick {intro_tick}")
    print(f"Price Crash: Tick {crash_tick if crash_tick != -1 else 'N/A'}")
    print(f"Peak Supply/Demand Ratio: {peak_ratio:.2f}")

    initial_pop = metrics["population"][0]
    final_pop = metrics["population"][-1]
    print(f"Population: {initial_pop} -> {final_pop} (+{final_pop - initial_pop})")

    success = True

    # Criteria 1: Supply/Demand >= 2.5
    if peak_ratio >= 2.5:
        print("[PASS] Supply Glut Verified (Ratio >= 2.5)")
    else:
        print(f"[FAIL] Supply Glut Failed (Peak Ratio {peak_ratio:.2f} < 2.5)")
        success = False

    # Criteria 2: Price Crash > 50%
    if crash_tick != -1:
         print("[PASS] Price Crash Verified")
    else:
         print("[FAIL] Price Crash Failed")
         success = False

    # Criteria 3: Population Boom
    if final_pop > initial_pop + 200:
        print("[PASS] Population Boom Verified")
    else:
        print(f"[FAIL] Population Boom Failed (Growth {final_pop - initial_pop} <= 200)")
        success = False

    if success:
        print("\nOVERALL: SUCCESS")
    else:
        print("\nOVERALL: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    verify_phase23()
