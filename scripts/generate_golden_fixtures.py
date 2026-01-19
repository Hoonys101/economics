import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Patch database to use a temporary file
import simulation.db.database
simulation.db.database.DATABASE_NAME = "golden_generation_temp.db"

from main import create_simulation
from scripts.fixture_harvester import FixtureHarvester
from simulation.db.database import close_db_connection

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("GoldenGenerator")

    # Ensure we are in the project root
    if not os.path.exists("config"):
        logger.error("❌ Please run this script from the project root directory: python scripts/generate_golden_fixtures.py")
        sys.exit(1)

    # Clean up any existing temp db
    if os.path.exists("golden_generation_temp.db"):
        os.remove("golden_generation_temp.db")

    logger.info("🚀 Starting Golden Fixture Generation...")

    try:
        # 1. Build Simulation
        # We use default config
        sim = create_simulation()

        harvester = FixtureHarvester(output_dir="tests/goldens")

        # 2. Tick 0: Initial State
        logger.info("📸 Capturing Tick 0 (Initial State)...")
        harvester.capture_agents(sim.households, sim.firms, tick=0)
        harvester.capture_config(sim.config_module)
        harvester.save_all("initial_state.json")

        # 3. Run to Tick 10 (Early Economy)
        logger.info("⏳ Running to Tick 10...")
        for _ in range(10):
            sim.run_tick()

        logger.info("📸 Capturing Tick 10 (Early Economy)...")
        harvester.capture_agents(sim.households, sim.firms, tick=10)
        harvester.save_all("early_economy.json")

        # 4. Run to Tick 100 (Stable Economy)
        logger.info("⏳ Running to Tick 100...")
        for _ in range(90):
            sim.run_tick()

        logger.info("📸 Capturing Tick 100 (Stable Economy)...")
        harvester.capture_agents(sim.households, sim.firms, tick=100)
        harvester.save_all("stable_economy.json")

        # Close repository explicitly
        sim.repository.close()

    except Exception as e:
        logger.error(f"❌ Error generating fixtures: {e}", exc_info=True)
    finally:
        # Cleanup
        close_db_connection()
        if os.path.exists("golden_generation_temp.db"):
            try:
                os.remove("golden_generation_temp.db")
                logger.info("🧹 Cleaned up temporary database.")
            except Exception as e:
                logger.warning(f"⚠️ Could not delete temporary database: {e}")

    logger.info("✅ Golden fixtures generated successfully!")

if __name__ == "__main__":
    main()
