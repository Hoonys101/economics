import pandas as pd

def analyze_results():
    try:
        baseline_df = pd.read_csv('results_baseline.csv')
        experiment_df = pd.read_csv('results_experiment.csv')
    except FileNotFoundError as e:
        print(f"Error: {e}. Please make sure both 'results_baseline.csv' and 'results_experiment.csv' exist.")
        return

    print("\n--- Baseline DataFrame Head ---")
    print(baseline_df.head())
    print("\n--- Baseline DataFrame Columns ---")
    print(baseline_df.columns)
    print("\n--- Experiment DataFrame Head ---")
    print(experiment_df.head())
    print("\n--- Experiment DataFrame Columns ---")
    print(experiment_df.columns)

    # Calculate metrics for baseline
    baseline_avg_price = baseline_df['food_avg_price'].mean()
    baseline_total_volume = baseline_df['food_trade_volume'].sum()

    # Calculate metrics for experiment
    experiment_avg_price = experiment_df['food_avg_price'].mean()
    experiment_total_volume = experiment_df['food_trade_volume'].sum()

    print("--- Supply-Demand Law Verification Results ---")
    print("\n--- Baseline Simulation ---")
    print(f"Average Food Price: {baseline_avg_price:.2f}")
    print(f"Total Food Trade Volume: {baseline_total_volume:.2f}")

    print("\n--- Experiment Simulation (Increased Food Supply) ---")
    print(f"Average Food Price: {experiment_avg_price:.2f}")
    print(f"Total Food Trade Volume: {experiment_total_volume:.2f}")

    # Verification
    price_decreased = experiment_avg_price < baseline_avg_price
    volume_increased = experiment_total_volume > baseline_total_volume

    print("\n--- Conclusion ---")
    if price_decreased and volume_increased:
        print("Success: The simulation correctly demonstrates the law of supply and demand.")
        print("Increased supply led to a lower price and higher trade volume.")
    elif price_decreased:
        print("Partial Success: Price decreased as expected, but trade volume did not increase.")
    elif volume_increased:
        print("Partial Success: Trade volume increased as expected, but price did not decrease.")
    else:
        print("Failure: The simulation does not correctly demonstrate the law of supply and demand.")
        print("Price did not decrease and trade volume did not increase with increased supply.")

if __name__ == '__main__':
    analyze_results()