import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_results():
    try:
        baseline_df = pd.read_csv('results_baseline.csv')
        experiment_df = pd.read_csv('results_experiment.csv')
    except FileNotFoundError as e:
        logging.error(f"Error: {e}. Please make sure both 'results_baseline.csv' and 'results_experiment.csv' exist.")
        return

    logging.info("\n--- Baseline DataFrame Head ---")
    logging.info(baseline_df.head())
    logging.info("\n--- Baseline DataFrame Columns ---")
    logging.info(baseline_df.columns)
    logging.info("\n--- Experiment DataFrame Head ---")
    logging.info(experiment_df.head())
    logging.info("\n--- Experiment DataFrame Columns ---")
    logging.info(experiment_df.columns)

    # Calculate metrics for baseline
    baseline_avg_price = baseline_df['food_avg_price'].mean()
    baseline_total_volume = baseline_df['food_trade_volume'].sum()

    # Calculate metrics for experiment
    experiment_avg_price = experiment_df['food_avg_price'].mean()
    experiment_total_volume = experiment_df['food_trade_volume'].sum()

    logging.info("--- Supply-Demand Law Verification Results ---")
    logging.info("\n--- Baseline Simulation ---")
    logging.info(f"Average Food Price: {baseline_avg_price:.2f}")
    logging.info(f"Total Food Trade Volume: {baseline_total_volume:.2f}")

    logging.info("\n--- Experiment Simulation (Increased Food Supply) ---")
    logging.info(f"Average Food Price: {experiment_avg_price:.2f}")
    logging.info(f"Total Food Trade Volume: {experiment_total_volume:.2f}")

    # Verification
    price_decreased = experiment_avg_price < baseline_avg_price
    volume_increased = experiment_total_volume > baseline_total_volume

    logging.info("\n--- Conclusion ---")
    if price_decreased and volume_increased:
        logging.info("Success: The simulation correctly demonstrates the law of supply and demand.")
        logging.info("Increased supply led to a lower price and higher trade volume.")
    elif price_decreased:
        logging.info("Partial Success: Price decreased as expected, but trade volume did not increase.")
    elif volume_increased:
        logging.info("Partial Success: Trade volume increased as expected, but price did not decrease.")
    else:
        logging.info("Failure: The simulation does not correctly demonstrate the law of supply and demand.")
        logging.info("Price did not decrease and trade volume did not increase with increased supply.")

if __name__ == '__main__':
    analyze_results()