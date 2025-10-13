import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_results():
    baseline_df = pd.read_csv('results_baseline.csv')
    increased_supply_df = pd.read_csv('results_experiment_increased.csv')
    decreased_supply_df = pd.read_csv('results_experiment_decreased.csv')

    logging.info("--- Supply and Demand Analysis Results ---")

    # Baseline
    logging.info("\nBaseline Scenario:")
    logging.info(f"  Average Food Price: {baseline_df['food_avg_price'].mean():.2f}")
    logging.info(f"  Average Food Consumption: {baseline_df['total_food_consumption'].mean():.2f}")

    # Increased Supply
    logging.info("\nIncreased Supply Scenario:")
    logging.info(f"  Average Food Price: {increased_supply_df['food_avg_price'].mean():.2f}")
    logging.info(f"  Average Food Consumption: {increased_supply_df['total_food_consumption'].mean():.2f}")

    # Decreased Supply
    logging.info("\nDecreased Supply Scenario:")
    logging.info(f"  Average Food Price: {decreased_supply_df['food_avg_price'].mean():.2f}")
    logging.info(f"  Average Food Consumption: {decreased_supply_df['total_food_consumption'].mean():.2f}")

    logging.info("\n--- Verification of Supply and Demand Law ---")
    logging.info("Expected: Increased supply -> Decreased price, Increased consumption")
    logging.info("Expected: Decreased supply -> Increased price, Decreased consumption")

    # Compare and verify
    baseline_price = baseline_df['food_avg_price'].mean()
    increased_supply_price = increased_supply_df['food_avg_price'].mean()
    decreased_supply_price = decreased_supply_df['food_avg_price'].mean()

    baseline_consumption = baseline_df['total_food_consumption'].mean()
    increased_supply_consumption = increased_supply_df['total_food_consumption'].mean()
    decreased_supply_consumption = decreased_supply_df['total_food_consumption'].mean()

    # Increased Supply vs Baseline
    if increased_supply_price < baseline_price and increased_supply_consumption > baseline_consumption:
        logging.info("\nIncreased Supply: VERIFIED (Price decreased, Consumption increased)")
    else:
        logging.info("\nIncreased Supply: NOT VERIFIED")
    logging.info(f"  Price Change: {increased_supply_price - baseline_price:.2f}")
    logging.info(f"  Consumption Change: {increased_supply_consumption - baseline_consumption:.2f}")

    # Decreased Supply vs Baseline
    if decreased_supply_price > baseline_price and decreased_supply_consumption < baseline_consumption:
        logging.info("\nDecreased Supply: VERIFIED (Price increased, Consumption decreased)")
    else:
        logging.info("\nDecreased Supply: NOT VERIFIED")
    logging.info(f"  Price Change: {decreased_supply_price - baseline_price:.2f}")
    logging.info(f"  Consumption Change: {decreased_supply_consumption - baseline_consumption:.2f}")

if __name__ == '__main__':
    analyze_results()
