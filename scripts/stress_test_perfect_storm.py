import sys
import os
import logging
import yaml
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Ensure modules are importable
sys.path.append(os.getcwd())

import config
from utils.simulation_builder import create_simulation
from modules.simulation.api import ShockConfigDTO
from modules.simulation.shock_injector import ShockInjector

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

    # 1. Reasoning Pareto Analysis
    query_pareto = """
    SELECT reason, COUNT(*) as frequency 
    FROM agent_thoughts 
    WHERE action_type IN ('BUY_FOOD', 'BUY_GOODS', 'CONSUME_FOOD') AND decision = 'REJECT' 
    GROUP BY reason ORDER BY frequency DESC;
    """
    pareto_df = pd.read_sql_query(query_pareto, conn)
    print("\n[TOP FAILURE MODES (REASONING)]")
    print(pareto_df if not pareto_df.empty else "No rejection data found.")

    # 2. Insolvency Context Check
    query_insolvent = """
    SELECT tick, agent_id, reason, json_extract(context_data, '$.cash') as cash, json_extract(context_data, '$.price') as price
    FROM agent_thoughts 
    WHERE reason = 'INSOLVENT' LIMIT 10;
    """
    insolvent_df = pd.read_sql_query(query_insolvent, conn)
    print("\n[INSOLVENCY SAMPLES]")
    print(insolvent_df if not insolvent_df.empty else "No insolvency events found.")

    # 3. Macro Trends
    query_macro = "SELECT tick, gdp, m2, cpi, transaction_count FROM tick_snapshots ORDER BY tick;"
    # Note: tick_snapshots might need to be populated by the engine or a separate probe.
    # If tick_snapshots is empty, we fall back to other indicators.
    
    conn.close()

def main():
    logger.info("Initializing [Operation Code Blue]: Perfect Storm Simulation")

    # Load configuration
    scenario_path = "config/scenarios/stress_test_wo148.yaml"
    scenario_config = load_config(scenario_path)

    # 1. Setup Config overrides (Extended Ticks for Recovery Observation)
    overrides = {
        "ENABLE_MONETARY_STABILIZER": scenario_config.get("ENABLE_MONETARY_STABILIZER", True),
        "ENABLE_FISCAL_STABILIZER": scenario_config.get("ENABLE_FISCAL_STABILIZER", True),
        "SIMULATION_TICKS": 400, # Increased for recovery phase
        "NUM_HOUSEHOLDS": scenario_config.get("NUM_HOUSEHOLDS", 100), # Higher density
        "NUM_FIRMS": scenario_config.get("NUM_FIRMS", 20),
        "SIMULATION_DATABASE_NAME": "percept_storm.db",
    }

    # 2. Create Simulation
    sim = create_simulation(overrides=overrides)
    db_path = overrides["SIMULATION_DATABASE_NAME"]

    # 3. Setup Shock
    shock_config = ShockConfigDTO(
        shock_start_tick=scenario_config["shock_start_tick"],
        shock_end_tick=scenario_config["shock_end_tick"],
        tfp_multiplier=scenario_config["tfp_multiplier"],
        baseline_tfp=scenario_config["baseline_tfp"]
    )
    injector = ShockInjector(shock_config, sim)

    # 4. Run Simulation Loop
    logger.info(f"Running simulation for {overrides['SIMULATION_TICKS']} ticks...")
    logger.info(f"Shock active between tick {shock_config.shock_start_tick} and {shock_config.shock_end_tick}")

    try:
        for tick in range(overrides["SIMULATION_TICKS"]):
            injector.apply(tick)
            sim.run_tick()
            
            if tick % 50 == 0:
                snapshot = sim.get_market_snapshot()
                logger.info(f"Tick {tick}: GDP={snapshot.gdp:.2f}, CPI={snapshot.cpi:.2f}")
                
            if getattr(sim, "gdp", 1.0) <= 0 and tick > shock_config.shock_start_tick:
                logger.warning(f"⚠️ SYSTEMIC COLLAPSE (GDP=0) detected at tick {tick}!")
                # We continue to log thoughts to see the 'death rattle'
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    except Exception as e:
        logger.error(f"Simulation crashed: {e}")
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
