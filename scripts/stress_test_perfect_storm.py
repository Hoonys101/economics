import sys
import os
import logging
import yaml
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from dotenv import load_dotenv

# Ensure modules are importable
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv()

import config
from modules.system.builders.simulation_builder import create_simulation
from modules.simulation.api import ShockConfigDTO
from modules.simulation.shock_injector import ShockInjector
from simulation.db.schema import create_tables

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PerfectStorm")

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_analysis(db_path: str):
    """Perform forensic analysis on ThoughtStream logs."""
    if not os.path.exists(db_path):
        logger.error(f"Database {db_path} not found for analysis.")
        return

    conn = sqlite3.connect(db_path)
    
    print("\n" + "="*50)
    print("🔬 PHENOMENA ANALYSIS: THOUGHTSTREAM AUTOPSY")
    print("="*50)

    # 1. Failure/Skip Reasons Analysis (Combined REJECT and SKIP)
    query_failures = """
    SELECT decision, reason, COUNT(*) as frequency
    FROM agent_thoughts 
    WHERE decision IN ('REJECT', 'SKIP')
       OR reason LIKE '%FAIL%'
       OR reason LIKE '%SKIP%'
    GROUP BY decision, reason
    ORDER BY frequency DESC;
    """
    try:
        failure_df = pd.read_sql_query(query_failures, conn)
        print("\n[FAILURE/SKIP REASONS]")
        print(failure_df if not failure_df.empty else "No failure/skip events found.")
    except Exception as e:
        print(f"\n[ANALYSIS ERROR] Could not query failure reasons: {e}")

    # 2. Insolvency Context Check
    query_insolvent = """
    SELECT tick, agent_id, reason, json_extract(context_data, '$.cash') as cash, json_extract(context_data, '$.price') as price
    FROM agent_thoughts 
    WHERE reason = 'INSOLVENT' LIMIT 10;
    """
    try:
        insolvent_df = pd.read_sql_query(query_insolvent, conn)
        print("\n[INSOLVENCY SAMPLES]")
        print(insolvent_df if not insolvent_df.empty else "No insolvency events found.")
    except Exception as e:
        print(f"\n[ANALYSIS ERROR] Could not query insolvency samples: {e}")

    # 3. Macro Trends
    query_macro = "SELECT tick, gdp, m2, cpi, transaction_count FROM tick_snapshots ORDER BY tick;"
    try:
        macro_df = pd.read_sql_query(query_macro, conn)
        print("\n[MACRO TRENDS SUMMARY]")
        print(macro_df.describe() if not macro_df.empty else "No macro data found.")
    except Exception as e:
        print(f"\n[MACRO TRENDS ERROR] Could not retrieve macro data: {e}")
    
    conn.close()

def main():
    logger.info("Initializing [Operation Code Blue]: Perfect Storm Simulation")

    # Load configuration
    scenario_path = "config/scenarios/stress_test_wo148.yaml"
    # Ensure scenario config exists, or fallback/mock it if missing (for robustness)
    if os.path.exists(scenario_path):
        scenario_config = load_config(scenario_path)
    else:
        logger.warning(f"{scenario_path} not found. Using defaults.")
        scenario_config = {
            "shock_start_tick": 100,
            "shock_end_tick": 200,
            "tfp_multiplier": 0.5,
            "baseline_tfp": 1.0,
            "ENABLE_MONETARY_STABILIZER": True,
            "ENABLE_FISCAL_STABILIZER": True,
            "NUM_HOUSEHOLDS": 100,
            "NUM_FIRMS": 20
        }

    # 1. Setup Config overrides (Extended Ticks for Recovery Observation)
    overrides = {
        "ENABLE_MONETARY_STABILIZER": scenario_config.get("ENABLE_MONETARY_STABILIZER", True),
        "ENABLE_FISCAL_STABILIZER": scenario_config.get("ENABLE_FISCAL_STABILIZER", True),
        "SIMULATION_TICKS": 400, # Increased for recovery phase
        "NUM_HOUSEHOLDS": scenario_config.get("NUM_HOUSEHOLDS", 100), # Higher density
        "NUM_FIRMS": scenario_config.get("NUM_FIRMS", 20),
        "SIMULATION_DATABASE_NAME": "percept_storm.db",
    }

    # Pre-initialize Database to ensure tables exist
    db_path = overrides["SIMULATION_DATABASE_NAME"]
    logger.info(f"Initializing database at {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        conn.close()
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return

    # 2. Create Simulation
    sim = create_simulation(overrides=overrides)

    # 3. Setup Shock
    shock_config = ShockConfigDTO(
        shock_start_tick=scenario_config.get("shock_start_tick", 100),
        shock_end_tick=scenario_config.get("shock_end_tick", 200),
        tfp_multiplier=scenario_config.get("tfp_multiplier", 0.5),
        baseline_tfp=scenario_config.get("baseline_tfp", 1.0)
    )
    injector = ShockInjector(shock_config, sim)

    # 4. Run Simulation Loop
    logger.info(f"Running simulation for {overrides['SIMULATION_TICKS']} ticks...")
    logger.info(f"Shock active between tick {shock_config['shock_start_tick']} and {shock_config['shock_end_tick']}")

    try:
        for tick in range(overrides["SIMULATION_TICKS"]):
            injector.apply(tick)
            sim.run_tick()
            
            # Use get_market_snapshot() correctly as it returns a TypedDict (dict access)
            if tick % 50 == 0:
                snapshot = sim.get_market_snapshot()
                logger.info(f"Tick {tick}: GDP={snapshot['gdp']:.2f}, CPI={snapshot['cpi']:.2f}")

            # Check for collapse (using fresh snapshot to ensure accuracy)
            if tick > shock_config['shock_start_tick']:
                current_snapshot = sim.get_market_snapshot()
                if current_snapshot['gdp'] <= 0:
                    logger.warning(f"⚠️ SYSTEMIC COLLAPSE (GDP=0) detected at tick {tick}!")
                    # We continue to log thoughts to see the 'death rattle'
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    except Exception as e:
        logger.error(f"Simulation crashed: {e}", exc_info=True)
    finally:
        sim.finalize_simulation()

    # 5. Analysis
    run_analysis(db_path)
    
    print("\n" + "="*50)
    print("🏁 SIMULATION COMPLETE")
    print(f"Results saved to: {db_path}")
    print("="*50)

if __name__ == "__main__":
    main()
