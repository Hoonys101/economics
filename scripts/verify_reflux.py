
import logging
import sys
import os
import matplotlib.pyplot as plt

# Ensure module path
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import run_simulation
from simulation.db.repository import SimulationRepository
from modules.analytics.loader import DataLoader
import config

# Setup Logging to capture DIVIDEND events
from utils.logging_manager import setup_logging
setup_logging()
logger = logging.getLogger("VERIFY_REFLUX")

def run_test_plan_a():
    """
    Test Plan A: 'The Reflux'
    - Income Tax = 0
    - Productivity = 20.0
    - Check for Dividend Logs
    - Check for Asset Golden Cross (Capital Income vs Labor Income)
    - Check Survival > 200 ticks
    """
    logger.info("Starting Test Plan A: Operation Reflux Verification")

    # 1. Configure
    # Override config for Laissez-Faire + Reflux
    overrides = {
        "INCOME_TAX_RATE": 0.0,
        "CORPORATE_TAX_RATE": 0.0, # Let them keep profit to distribute
        "SALES_TAX_RATE": 0.0,
        "FIRM_PRODUCTIVITY_FACTOR": 20.0,
        "FIRM_MAINTENANCE_FEE": 50.0,
        "SIMULATION_TICKS": 400, # Goal is > 200
        "INITIAL_FIRM_CAPITAL_MEAN": 10000.0, # Same as Laissez-Faire
    }
    
    # Apply overrides (Hack: modify config directly as main.run_simulation doesn't support all overrides easily via args)
    # But main.create_simulation does.
    # main.run_simulation accepts specific args, but we might need to modify config module.
    for k, v in overrides.items():
        setattr(config, k, v)
    
    # 2. Run Simulation
    output_file = "reflux_test_results.csv"
    try:
        run_simulation(output_filename=output_file)
    except Exception as e:
        logger.error(f"Simulation crashed: {e}")
        return

    # 3. Analyze Results
    repo = SimulationRepository()
    run_id = repo._get_latest_run_id()
    loader = DataLoader("simulation_data.db")
    eco_df = loader.load_economic_indicators(run_id=run_id)
    
    if eco_df.empty:
        logger.error("No economic data found.")
        return

    # 3.1 Check Log/Event Evidence (Dividends)
    # We can't grep logs easily from here unless we read the log file.
    # But we can check 'total_capital_income' from eco_df.
    
    total_labor = eco_df["total_labor_income"].sum()
    total_capital = eco_df["total_capital_income"].sum()
    
    logger.info(f"Total Labor Income: {total_labor:,.2f}")
    logger.info(f"Total Capital Income: {total_capital:,.2f}")
    
    if total_capital > 0:
        logger.info("SUCCESS: Capital Income detected (Dividends flowing).")
    else:
        logger.error("FAILURE: No Capital Income detected.")
        
    # 3.2 Check Golden Cross
    # Plot Income Composition
    plt.figure(figsize=(10, 6))
    plt.plot(eco_df.index, eco_df["total_labor_income"], label="Labor Income", color="blue")
    plt.plot(eco_df.index, eco_df["total_capital_income"], label="Capital Income", color="red")
    plt.title("Income Composition: Labor vs Capital")
    plt.xlabel("Tick")
    plt.ylabel("Income")
    plt.legend()
    plt.grid(True)
    plt.savefig("reports/figures/income_composition_reflux.png")
    logger.info("Generated 'reports/figures/income_composition_reflux.png'")
    
    # 3.3 Check Survival
    # Deaths?
    # Get attrition
    attrition = repo.get_attrition_counts(start_tick=0, end_tick=400, run_id=run_id)
    logger.info(f"Attrition: {attrition}")
    
    final_tick = eco_df.index.max()
    logger.info(f"Simulation reached tick: {final_tick}")
    
    if final_tick >= 200:
        logger.info("SUCCESS: Survived beyond 200 ticks.")
    else:
        logger.warning(f"WARNING: Colllapsed at {final_tick} ticks.")

    repo.close()

if __name__ == "__main__":
    run_test_plan_a()
