import main
import config

def run_experiment():
    # Store original config value
    original_initial_firm_inventory_mean = config.INITIAL_FIRM_INVENTORY_MEAN

    # 1. Baseline run
    print("--- Running Baseline Simulation ---")
    main.run_simulation(output_filename='results_baseline.csv')

    # 2. Experiment run with increased food inventory
    print("--- Running Experiment Simulation (Increased Food Inventory) ---")
    
    # Temporarily modify config for the experiment
    experimental_initial_firm_inventory_mean = original_initial_firm_inventory_mean * 5 # Increase by 5 times
    
    main.run_simulation(initial_firm_inventory_mean=experimental_initial_firm_inventory_mean, output_filename='results_experiment.csv')

    # Restore original config value
    config.INITIAL_FIRM_INVENTORY_MEAN = original_initial_firm_inventory_mean

if __name__ == '__main__':
    run_experiment()