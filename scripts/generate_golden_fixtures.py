import sys
import os
from pathlib import Path
import logging

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Mock matplotlib to prevent "no display name" errors on headless systems
import unittest.mock

sys.modules["matplotlib"] = unittest.mock.MagicMock()
sys.modules["matplotlib.pyplot"] = unittest.mock.MagicMock()

try:
    from main import create_simulation
    from scripts.fixture_harvester import FixtureHarvester
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)


def generate_golden_fixtures():
    print("🚀 Starting Golden Fixture Generation...")

    # Configure logging to avoid spam
    logging.basicConfig(level=logging.ERROR)

    # Create simulation
    try:
        sim = create_simulation()
    except Exception as e:
        print(f"❌ Failed to create simulation: {e}")
        import traceback

        traceback.print_exc()
        return

    harvester = FixtureHarvester(output_dir="tests/goldens")

    # Target ticks to capture
    capture_schedule = {
        0: "initial_state.json",
        10: "early_economy.json",
        100: "stable_economy.json",
    }

    max_tick = max(capture_schedule.keys())

    print(f"⏳ Running simulation up to tick {max_tick}...")

    # Run simulation loop

    while sim.time <= max_tick:
        current_tick = sim.time

        if current_tick in capture_schedule:
            filename = capture_schedule[current_tick]
            print(f"📸 Capturing state at tick {current_tick} -> {filename}")

            try:
                harvester.capture_agents(sim.households, sim.firms, tick=current_tick)
                harvester.capture_config(sim.config_module)
                harvester.save_all(filename)
            except Exception as e:
                print(f"❌ Failed to capture fixture at tick {current_tick}: {e}")
                import traceback

                traceback.print_exc()

        if sim.time < max_tick:
            try:
                sim.run_tick()
            except Exception as e:
                print(f"❌ Simulation failed at tick {current_tick}: {e}")
                import traceback

                traceback.print_exc()
                break
        else:
            break

    print("✅ Golden Fixture Generation Complete.")


if __name__ == "__main__":
    generate_golden_fixtures()
