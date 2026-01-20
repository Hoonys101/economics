"""
Diagnostic Script for Economic Failure Analysis.
Focuses on Production vs Consumption gap and Inventory depletion.
"""
import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
import logging

# Ensure module path
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from modules.analytics.loader import DataLoader

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_diagnosis(db_path="simulation_data.db", output_dir="reports/figures"):
    logger.info("Starting failure diagnosis...")
    loader = DataLoader(db_path)
    os.makedirs(output_dir, exist_ok=True)

    eco_df = loader.load_economic_indicators(run_id="latest")
    
    if eco_df.empty:
        logger.error("No data found.")
        return

    # 1. Production vs Consumption Gap
    plt.figure(figsize=(12, 6))
    plt.plot(eco_df.index, eco_df["total_production"], label="Production", color="blue", alpha=0.7)
    plt.plot(eco_df.index, eco_df["total_consumption"], label="Consumption", color="orange", alpha=0.7)
    plt.fill_between(eco_df.index, eco_df["total_production"], eco_df["total_consumption"], 
                     where=(eco_df["total_production"] < eco_df["total_consumption"]),
                     color='red', alpha=0.3, label="Deficit (Inventory Drain)")
    plt.title("Production vs Consumption Gap")
    plt.xlabel("Tick")
    plt.ylabel("Units")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "failure_gap.png"))
    plt.close()

    # 2. Inventory Levels
    plt.figure(figsize=(12, 6))
    plt.plot(eco_df.index, eco_df["total_inventory"], label="Total Inventory", color="brown")
    plt.axhline(y=0, color='black', linestyle='--')
    plt.title("Total System Inventory (Market Feed)")
    plt.xlabel("Tick")
    plt.ylabel("Units")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "failure_inventory.png"))
    plt.close()

    # 3. Cash Flow Imbalance
    plt.figure(figsize=(12, 6))
    plt.stackplot(eco_df.index, eco_df["total_household_assets"], eco_df["total_firm_assets"], 
                  labels=["Household Assets", "Firm Assets"], colors=["lightblue", "salmon"])
    plt.title("Asset Distribution: Money Magnet Effect")
    plt.xlabel("Tick")
    plt.ylabel("Currency")
    plt.legend(loc='upper right')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "failure_assets.png"))
    plt.close()

    logger.info(f"Diagnosis complete. Figures saved in {output_dir}")

if __name__ == "__main__":
    run_diagnosis()
