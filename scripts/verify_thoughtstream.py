import sys
import os
import logging
import sqlite3
import json

# Ensure modules are importable
sys.path.append(os.getcwd())

import config
import simulation.db.database
from modules.system.builders.simulation_builder import create_simulation

# Configure logging
logging.basicConfig(level=logging.ERROR) # Suppress info/debug logs
logger = logging.getLogger("VerifyThoughtStream")
logger.setLevel(logging.INFO)

def main():
    db_name = "verification_test.db"

    # Remove existing db if any
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
        except PermissionError:
            logger.warning(f"Could not remove existing DB {db_name}. Is it open?")

    # Patch the database name globally for DatabaseManager
    simulation.db.database.DATABASE_NAME = db_name

    overrides = {
        "NUM_HOUSEHOLDS": 5,
        "NUM_FIRMS": 1,
        "SIMULATION_TICKS": 10,
        "BATCH_SAVE_INTERVAL": 1,
        "SIMULATION_DATABASE_NAME": db_name,

        # Force insolvency and hunger
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 0.0,
        "INITIAL_HOUSEHOLD_ASSETS_RANGE": 0.0,
        "INITIAL_HOUSEHOLD_FOOD_INVENTORY": 0.0,
        "INITIAL_HOUSEHOLD_NEEDS_MEAN": {
             "survival": 80.0,
             "survival_need": 80.0,
             "asset": 10.0,
             "social": 20.0,
             "improvement": 10.0,
             "recognition_need": 20.0,
             "growth_need": 10.0,
             "wealth_need": 10.0,
             "imitation_need": 15.0,
             "labor_need": 0.0,
             "child_rearing_need": 0.0,
             "quality": 0.0,
        },
        "SURVIVAL_NEED_CONSUMPTION_THRESHOLD": 50.0,
        "DEFAULT_FALLBACK_PRICE": 10.0, # Price to compare against assets (0)

        # Disable other systems that might give money
        "INITIAL_EMPLOYMENT_RATE": 0.0,
        "UNEMPLOYMENT_BENEFIT_RATIO": 0.0,
    }

    logger.info("Creating simulation with forced insolvency...")
    sim = create_simulation(overrides=overrides)

    logger.info("Running simulation for 10 ticks...")
    try:
        for tick in range(10):
            sim.run_tick()
    except Exception as e:
        logger.error(f"Simulation failed during run: {e}")
        # Continue to check DB just in case

    sim.finalize_simulation()

    logger.info("Verifying database contents...")

    if not os.path.exists(db_name):
        logger.error(f"Database file {db_name} was not created.")
        sys.exit(1)

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Check agent_thoughts for REJECT decisions
    try:
        cursor.execute("SELECT tick, agent_id, decision, reason, context_data FROM agent_thoughts WHERE decision = 'REJECT'")
        rows = cursor.fetchall()

        if not rows:
            logger.error("Verification FAILED: No 'REJECT' decisions found in agent_thoughts.")
            # Let's check if there are ANY thoughts
            cursor.execute("SELECT count(*) FROM agent_thoughts")
            count = cursor.fetchone()[0]
            logger.info(f"Total rows in agent_thoughts: {count}")

            conn.close()
            sys.exit(1)

        logger.info(f"Verification PASSED: Found {len(rows)} 'REJECT' decisions.")
        for row in rows[:3]: # Print first 3
            logger.info(f"Sample: Tick={row[0]}, Agent={row[1]}, Reason={row[3]}, Context={row[4]}")

    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

    # Cleanup
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
            logger.info("Cleaned up database file.")
        except PermissionError:
             logger.warning(f"Could not clean up {db_name}.")

if __name__ == "__main__":
    main()
