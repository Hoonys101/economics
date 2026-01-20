"""
Visualization Script for Economy Simulation.
Generates charts based on simulation data.
"""
import sys
from pathlib import Path
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging

# Ensure module path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from modules.analytics.loader import DataLoader

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_charts(db_path="simulation_data.db", output_dir="reports/figures"):
    logger.info("Starting visualization process...")

    loader = DataLoader(db_path)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load Data
    logger.info("Loading data...")
    eco_df = loader.load_economic_indicators(run_id="latest")
    agent_df = loader.load_agent_states(run_id="latest")
    fiscal_data = loader.load_fiscal_history("reports/fiscal_history.json")

    if eco_df.empty:
        logger.error("No economic indicators found. Aborting.")
        return

    # --- Chart 1: Macro Overview ---
    logger.info("Generating Macro Overview...")
    fig, axes = plt.subplots(3, 1, figsize=(10, 15), sharex=True)

    # Subplot 1: Total Money Supply
    # Money Supply = Household Assets + Firm Assets + (Government Assets? usually excluded or separate)
    # eco_df usually has total_household_assets, total_firm_assets.
    # Total Money = HH + Firm + Bank (if available) + Reflux (if available).
    # Let's use what we have in eco_df.

    money_supply = eco_df["total_household_assets"] + eco_df["total_firm_assets"]
    axes[0].plot(eco_df.index, money_supply, label="Total Money (HH+Firm)", color="green")
    axes[0].set_title("Total Money Supply")
    axes[0].set_ylabel("Currency")
    axes[0].grid(True)
    axes[0].legend()

    # Subplot 2: GDP (Total Production)
    axes[1].plot(eco_df.index, eco_df["total_production"], label="GDP (Production)", color="blue")
    axes[1].set_title("GDP (Total Production)")
    axes[1].set_ylabel("Units")
    axes[1].grid(True)
    axes[1].legend()

    # Subplot 3: Average Goods Price
    # eco_df has avg_goods_price
    axes[2].plot(eco_df.index, eco_df["avg_goods_price"], label="Avg Price", color="red")
    axes[2].set_title("Average Goods Price")
    axes[2].set_xlabel("Tick")
    axes[2].set_ylabel("Price")
    axes[2].grid(True)
    axes[2].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "macro_overview.png"))
    plt.close()

    # --- Chart 2: Inequality GINI ---
    logger.info("Generating Inequality GINI...")
    # Calculate GINI per tick for Households
    gini_series = []
    ticks = sorted(agent_df["time"].unique())

    for tick in ticks:
        # Filter households
        tick_data = agent_df[(agent_df["time"] == tick) & (agent_df["agent_type"] == "household")]
        assets = tick_data["assets"].values
        if len(assets) > 0:
            gini = gini_coefficient(assets)
            gini_series.append({"time": tick, "gini": gini})

    gini_df = pd.DataFrame(gini_series)
    if not gini_df.empty:
        gini_df.set_index("time", inplace=True)

        plt.figure(figsize=(10, 6))
        plt.plot(gini_df.index, gini_df["gini"], label="Wealth GINI", color="purple")
        plt.title("Wealth Inequality (GINI Coefficient)")
        plt.xlabel("Tick")
        plt.ylabel("GINI")
        plt.grid(True)
        plt.legend()
        plt.savefig(os.path.join(output_dir, "inequality_gini.png"))
        plt.close()

        final_gini = gini_df["gini"].iloc[-1]
    else:
        logger.warning("No household data for GINI calculation.")
        final_gini = None

    # --- Chart 3: Fiscal Status ---
    logger.info("Generating Fiscal Status...")

    # Government Assets vs Debt
    # We need government assets history. agent_states has it.
    gov_states = agent_df[agent_df["agent_type"] == "government"]

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot Assets (Left Axis)
    line1 = None
    if not gov_states.empty:
        # Sort by time
        gov_states = gov_states.sort_values("time")
        line1, = ax1.plot(gov_states["time"], gov_states["assets"], label="Gov Assets", color="blue")
    elif "welfare" in fiscal_data and "assets" in fiscal_data["welfare"].columns:
        # Fallback to fiscal_history.json
        assets_data = fiscal_data["welfare"]["assets"]
        line1, = ax1.plot(assets_data.index, assets_data, label="Gov Assets (Log)", color="blue")
    else:
        logger.warning("No government assets data found.")

    if line1:
        ax1.set_xlabel("Tick")
        ax1.set_ylabel("Assets", color="blue")
        ax1.tick_params(axis='y', labelcolor="blue")

    # Plot Debt (Right Axis) if available
    line2 = None
    if "welfare" in fiscal_data and "debt" in fiscal_data["welfare"].columns:
        ax2 = ax1.twinx()
        debt_data = fiscal_data["welfare"]["debt"]
        line2, = ax2.plot(debt_data.index, debt_data, label="Total Debt", color="red", linestyle="--")
        ax2.set_ylabel("Debt", color="red")
        ax2.tick_params(axis='y', labelcolor="red")

    # Legend
    lines = [l for l in [line1, line2] if l is not None]
    labels = [l.get_label() for l in lines]
    if lines:
        ax1.legend(lines, labels, loc="upper left")

    plt.title("Government Assets vs Total Debt")
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "fiscal_status_assets.png"))
    plt.close()

    # Tax Revenue vs Welfare Spending
    if "tax" in fiscal_data and "welfare" in fiscal_data:
        tax_df = fiscal_data["tax"]
        welfare_df = fiscal_data["welfare"]

        # Merge on index (tick)
        fiscal_combined = pd.merge(tax_df, welfare_df, left_index=True, right_index=True, how="outer").fillna(0)

        plt.figure(figsize=(12, 6))

        # Tax Revenue (Stacked if multiple columns exist, else total)
        # tax_df columns might be "total", "income_tax", "wealth_tax", ...
        # Use "total" if available, or sum others
        if "total" in tax_df.columns:
            plt.plot(fiscal_combined.index, fiscal_combined["total"], label="Total Tax Revenue", color="green")

        # Welfare Spending
        if "welfare" in welfare_df.columns:
            plt.plot(fiscal_combined.index, fiscal_combined["welfare"], label="Welfare Spending", color="orange", linestyle="--")
        if "stimulus" in welfare_df.columns:
            plt.plot(fiscal_combined.index, fiscal_combined["stimulus"], label="Stimulus", color="red", linestyle=":")

        plt.title("Fiscal Flows: Tax Revenue vs Welfare")
        plt.xlabel("Tick")
        plt.ylabel("Amount")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, "fiscal_status.png"))
        plt.close()
    else:
        logger.warning("Fiscal history data missing. Skipping Fiscal Status chart.")

    logger.info("Visualization complete. Check reports/figures/")

    # --- Console Report ---
    print("\n=== Economy Visualization Report ===")
    if not eco_df.empty:
        final_gdp = eco_df["total_production"].iloc[-1]
        final_price = eco_df["avg_goods_price"].iloc[-1]
        final_money = money_supply.iloc[-1]
        print(f"Final GDP: {final_gdp:,.2f}")
        print(f"Final Money Supply: {final_money:,.2f}")
        print(f"Final Avg Goods Price: {final_price:.2f}")

    if final_gini is not None:
        print(f"Final GINI: {final_gini:.4f}")

    if "welfare" in fiscal_data and "debt" in fiscal_data["welfare"].columns:
        final_debt = fiscal_data["welfare"]["debt"].iloc[-1]
        print(f"Final Govt Debt: {final_debt:,.2f}")
        if not gov_states.empty:
            final_assets = gov_states["assets"].iloc[-1]
            print(f"Final Govt Assets: {final_assets:,.2f}")
            if final_assets > 0:
                print(f"Debt/Assets Ratio: {final_debt/final_assets:.2f}")

def gini_coefficient(x):
    """Compute Gini coefficient of array of values"""
    import numpy as np
    diffsum = 0
    for i, xi in enumerate(x[:-1], 1):
        diffsum += np.sum(np.abs(xi - x[i:]))
    return diffsum / (len(x)**2 * np.mean(x))

if __name__ == "__main__":
    generate_charts()
