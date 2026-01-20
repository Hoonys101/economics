import main
import config
import pandas as pd
import sqlite3
import json
import logging


def extract_and_save_economic_indicators(db_path: str, output_csv_path: str):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT tick, global_economic_indicators FROM simulation_states ORDER BY tick"
        data = conn.execute(query).fetchall()

        records = []
        for tick, indicators_json in data:
            if indicators_json:
                indicators = json.loads(indicators_json)
                record = {
                    "time": tick,
                    "food_avg_price": indicators.get("food_avg_price"),
                    "food_trade_volume": indicators.get("food_trade_volume"),
                    "total_food_consumption": indicators.get("total_food_consumption"),
                }
                records.append(record)

        df = pd.DataFrame(records)
        df.to_csv(output_csv_path, index=False)
        logging.info(f"Extracted economic indicators to {output_csv_path}")
    except Exception as e:
        logging.error(
            f"Error extracting economic indicators from {db_path} to {output_csv_path}: {e}"
        )
    finally:
        if conn:
            conn.close()


def run_experiment():
    # Store original config value
    original_food_supply_modifier = config.FOOD_SUPPLY_MODIFIER
    db_path = "simulation_data.db"

    # Configure logging to reduce console output during simulation runs
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    simulation_logger = logging.getLogger("simulation")
    original_simulation_log_level = simulation_logger.level
    simulation_logger.setLevel(logging.DEBUG)

    # 1. Baseline run
    logging.info("--- Running Baseline Simulation (100 Ticks) ---")
    config.FOOD_SUPPLY_MODIFIER = 1.0  # No change for baseline
    config.SIMULATION_TICKS = 100
    main.run_simulation(output_filename="results_baseline.csv")
    extract_and_save_economic_indicators(db_path, "results_baseline.csv")

    # 2. Experiment run with increased food supply
    logging.info("--- Running Experiment Simulation (Increased Food Supply) ---")

    # Temporarily modify config for the experiment
    config.FOOD_SUPPLY_MODIFIER = 1.5  # 50% increase for experiment 1
    config.SIMULATION_TICKS = 100
    main.run_simulation(output_filename="results_experiment_increased.csv")
    extract_and_save_economic_indicators(db_path, "results_experiment_increased.csv")

    # 3. Experiment run with decreased food supply
    logging.info("--- Running Experiment Simulation (Decreased Food Supply) ---")

    # Temporarily modify config for the experiment
    config.FOOD_SUPPLY_MODIFIER = 0.5  # 50% decrease for experiment 2
    main.run_simulation(output_filename="results_experiment_decreased.csv")
    extract_and_save_economic_indicators(db_path, "results_experiment_decreased.csv")

    # Restore original config value
    config.FOOD_SUPPLY_MODIFIER = original_food_supply_modifier

    # Restore original simulation logger level
    simulation_logger.setLevel(original_simulation_log_level)

    # Analyze the results
    logging.info("\n--- Analyzing Experiment Results ---")



if __name__ == "__main__":
    run_experiment()
