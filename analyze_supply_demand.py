import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_supply_demand(baseline_file, increased_supply_file, decreased_supply_file):
    logging.info(f"Analyzing {baseline_file}, {increased_supply_file}, and {decreased_supply_file} for supply-demand\nverification...")

    try:
        df_baseline = pd.read_csv(baseline_file)
        df_increased_supply = pd.read_csv(increased_supply_file)
        df_decreased_supply = pd.read_csv(decreased_supply_file)
    except Exception as e:
        logging.error(f"Error reading CSV files: {e}")
        return

    logging.info("\n--- Baseline Results ---")
    logging.info(df_baseline[['food_avg_price', 'food_trade_volume']].describe())

    logging.info("\n--- Experiment 1 Results (Increased Food Supply) ---")
    logging.info(df_increased_supply[['food_avg_price', 'food_trade_volume']].describe())

    logging.info("\n--- Experiment 2 Results (Decreased Food Supply) ---")
    logging.info(df_decreased_supply[['food_avg_price', 'food_trade_volume']].describe())

    # Calculate averages for comparison
    avg_price_baseline = df_baseline['food_avg_price'].mean()
    avg_volume_baseline = df_baseline['food_trade_volume'].mean()

    avg_price_increased = df_increased_supply['food_avg_price'].mean()
    avg_volume_increased = df_increased_supply['food_trade_volume'].mean()

    avg_price_decreased = df_decreased_supply['food_avg_price'].mean()
    avg_volume_decreased = df_decreased_supply['food_trade_volume'].mean()

    logging.info("\n--- Supply-Demand Verification ---")
    logging.info(f"Baseline Average Food Price: {avg_price_baseline:.2f}")
    logging.info(f"Experiment 1 (Increased Supply) Average Food Price: {avg_price_increased:.2f}")
    logging.info(f"Experiment 2 (Decreased Supply) Average Food Price: {avg_price_decreased:.2f}")
    logging.info(f"Baseline Average Food Trade Volume: {avg_volume_baseline:.2f}")
    logging.info(f"Experiment 1 (Increased Supply) Average Food Trade Volume: {avg_volume_increased:.2f}")
    logging.info(f"Experiment 2 (Decreased Supply) Average Food Trade Volume: {avg_volume_decreased:.2f}")

    logging.info("\n--- Observations (Increased Supply) ---")
    if avg_price_increased < avg_price_baseline:
        logging.info("Observation: Average food price DECREASED in Experiment 1 (as expected with increased supply).")
    else:
        logging.info("Observation: Average food price DID NOT DECREASE in Experiment 1 (unexpected).")

    if avg_volume_increased > avg_volume_baseline:
        logging.info("Observation: Average food trade volume INCREASED in Experiment 1 (as expected with increased supply).")
    else:
        logging.info("Observation: Average food trade volume DID NOT INCREASE in Experiment 1 (unexpected).")

    logging.info("\n--- Observations (Decreased Supply) ---")
    if avg_price_decreased > avg_price_baseline:
        logging.info("Observation: Average food price INCREASED in Experiment 2 (as expected with decreased supply).")
    else:
        logging.info("Observation: Average food price DID NOT INCREASE in Experiment 2 (unexpected).")

    if avg_volume_decreased < avg_volume_baseline:
        logging.info("Observation: Average food trade volume DECREASED in Experiment 2 (as expected with decreased supply).")
    else:
        logging.info("Observation: Average food trade volume DID NOT DECREASE in Experiment 2 (unexpected).")

    logging.info("\n--- Conclusion ---")
    overall_support = True
    if not (avg_price_increased < avg_price_baseline and avg_volume_increased > avg_volume_baseline):
        overall_support = False
    if not (avg_price_decreased > avg_price_baseline and avg_volume_decreased < avg_volume_baseline):
        overall_support = False

    if overall_support:
        logging.info("The simulation results generally support the law of supply and demand for 'food' across both\nexperiments.")
    else:
        logging.info("The simulation results do NOT fully support the law of supply and demand for 'food'. Further\ninvestigation may be needed.")

if __name__ == "__main__":
    baseline_file = "results_baseline.csv"
    increased_supply_file = "results_experiment_increased.csv"
    decreased_supply_file = "results_experiment_decreased.csv"
    analyze_supply_demand(baseline_file, increased_supply_file, decreased_supply_file)
