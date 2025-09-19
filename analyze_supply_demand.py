import pandas as pd

def analyze_supply_demand(baseline_file, experiment_file):
    print(f"Analyzing {baseline_file} and {experiment_file} for supply-demand verification...")

    try:
        df_baseline = pd.read_csv(baseline_file)
        df_experiment = pd.read_csv(experiment_file)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        return

    print("\n--- Baseline Results ---")
    print(df_baseline[['food_avg_price', 'food_trade_volume']].describe())

    print("\n--- Experiment Results (Increased Food Supply) ---")
    print(df_experiment[['food_avg_price', 'food_trade_volume']].describe())

    # Calculate averages for comparison
    avg_price_baseline = df_baseline['food_avg_price'].mean()
    avg_volume_baseline = df_baseline['food_trade_volume'].mean()

    avg_price_experiment = df_experiment['food_avg_price'].mean()
    avg_volume_experiment = df_experiment['food_trade_volume'].mean()

    print("\n--- Supply-Demand Verification ---")
    print(f"Baseline Average Food Price: {avg_price_baseline:.2f}")
    print(f"Experiment Average Food Price: {avg_price_experiment:.2f}")
    print(f"Baseline Average Food Trade Volume: {avg_volume_baseline:.2f}")
    print(f"Experiment Average Food Trade Volume: {avg_volume_experiment:.2f}")

    if avg_price_experiment < avg_price_baseline:
        print("Observation: Average food price DECREASED in the experiment (as expected with increased supply).")
    else:
        print("Observation: Average food price DID NOT DECREASE in the experiment (unexpected).")

    if avg_volume_experiment > avg_volume_baseline:
        print("Observation: Average food trade volume INCREASED in the experiment (as expected with increased supply).")
    else:
        print("Observation: Average food trade volume DID NOT INCREASE in the experiment (unexpected).")

    print("\n--- Conclusion ---")
    if avg_price_experiment < avg_price_baseline and avg_volume_experiment > avg_volume_baseline:
        print("The simulation results generally support the law of supply and demand for 'food'.")
    else:
        print("The simulation results do NOT fully support the law of supply and demand for 'food'. Further investigation may be needed.")

if __name__ == "__main__":
    baseline_file = "results_baseline.csv"
    experiment_file = "results_experiment.csv"
    analyze_supply_demand(baseline_file, experiment_file)
