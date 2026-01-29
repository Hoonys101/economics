import sys
import os
import json
import logging
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import Matplotlib after sys.path (if it's in the env)
try:
    import matplotlib.pyplot as plt
except ImportError:
    print("⚠️ Matplotlib not found. Attempting to install...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt

# Patch Database to use Memory
import simulation.db.database
simulation.db.database.DATABASE_NAME = ":memory:"

from main import create_simulation
import config

# Setup Logging
# main.py sets up logging, but we can get a logger for this script
logger = logging.getLogger("SoftLandingVerification")

@dataclass
class SimulationResults:
    gdp: List[float] = field(default_factory=list)
    inflation: List[float] = field(default_factory=list)
    unemployment: List[float] = field(default_factory=list)
    gini: List[float] = field(default_factory=list)
    interest_rate: List[float] = field(default_factory=list)
    tax_revenue: List[float] = field(default_factory=list)

def run_verification_simulation(enable_stabilizers: bool, ticks: int = 1000) -> SimulationResults:
    logger.info(f"Starting simulation with Stabilizers={'ENABLED' if enable_stabilizers else 'DISABLED'}")

    overrides = {
        "ENABLE_MONETARY_STABILIZER": enable_stabilizers,
        "ENABLE_FISCAL_STABILIZER": enable_stabilizers,
        "SIMULATION_TICKS": ticks,
        "RANDOM_SEED": 42, # Ensure reproducibility
        "BATCH_SAVE_INTERVAL": 10000, # Disable frequent db saves to speed up
        # We want to ensure we have enough history for metrics
        "TICKS_PER_YEAR": 100
    }

    sim = create_simulation(overrides=overrides)

    results = SimulationResults()

    # Determine base price for inflation calc from config
    base_price = config.GOODS_INITIAL_PRICE.get("basic_food", 5.0)

    # Run Loop
    for tick in range(ticks):
        sim.run_tick()

        # Collect Metrics
        # GDP
        metrics = sim.tracker.get_latest_indicators()
        gdp = metrics.get("total_production", 0.0)
        results.gdp.append(gdp)

        # Inflation (Price Level)
        avg_price = metrics.get("avg_goods_price", base_price)
        results.inflation.append(avg_price)

        # Unemployment
        unemployed_count = sum(1 for h in sim.households if not h.is_employed and h.is_active)
        active_count = sum(1 for h in sim.households if h.is_active)
        unemp_rate = unemployed_count / active_count if active_count > 0 else 0.0
        results.unemployment.append(unemp_rate)

        # Gini
        assets = [h.assets for h in sim.households if getattr(h, "is_active", True)]
        gini = sim.inequality_tracker.calculate_gini_coefficient(assets)
        results.gini.append(gini)

        # Interest Rate
        results.interest_rate.append(sim.central_bank.get_base_rate())

        # Tax Revenue
        # finalize_tick pushes to history. We can read from history.
        if sim.government.tax_history:
            results.tax_revenue.append(sim.government.tax_history[-1].get("total", 0.0))
        else:
             results.tax_revenue.append(0.0)

    # Finalize
    sim.finalize_simulation()

    return results

def analyze_results(baseline: SimulationResults, stabilized: SimulationResults):
    logger.info("Analyzing Results...")

    # 1. Volatility (Standard Deviation of Growth Rates)
    def calc_volatility(series):
        if not series: return 0.0
        arr = np.array(series)
        # Avoid division by zero
        arr = np.where(arr == 0, 0.001, arr)
        growth = np.diff(arr) / arr[:-1]
        return np.std(growth)

    gdp_vol_base = calc_volatility(baseline.gdp)
    gdp_vol_stab = calc_volatility(stabilized.gdp)

    inf_vol_base = calc_volatility(baseline.inflation)
    inf_vol_stab = calc_volatility(stabilized.inflation)

    logger.info(f"GDP Volatility: Baseline={gdp_vol_base:.4f}, Stabilized={gdp_vol_stab:.4f}")
    logger.info(f"Inflation Volatility: Baseline={inf_vol_base:.4f}, Stabilized={inf_vol_stab:.4f}")

    # 2. Recessions
    def count_recessions(series):
        if not series: return 0, 0
        arr = np.array(series)
        growth = np.diff(arr) / np.where(arr[:-1]==0, 1, arr[:-1])
        # Recession: >= 2 consecutive ticks of negative growth
        is_negative = growth < 0
        recession_count = 0
        recession_ticks = 0
        consecutive = 0
        in_recession = False

        for neg in is_negative:
            if neg:
                consecutive += 1
                if consecutive >= 2:
                    recession_ticks += 1
                    if not in_recession:
                        recession_count += 1
                        in_recession = True
            else:
                consecutive = 0
                in_recession = False
        return recession_count, recession_ticks

    rec_count_base, rec_dur_base = count_recessions(baseline.gdp)
    rec_count_stab, rec_dur_stab = count_recessions(stabilized.gdp)

    logger.info(f"Recessions: Baseline={rec_count_base} (Duration: {rec_dur_base}), Stabilized={rec_count_stab} (Duration: {rec_dur_stab})")

    return {
        "baseline": {
            "gdp_volatility": float(gdp_vol_base),
            "inflation_volatility": float(inf_vol_base),
            "recession_count": int(rec_count_base),
            "recession_duration": int(rec_dur_base)
        },
        "stabilized": {
            "gdp_volatility": float(gdp_vol_stab),
            "inflation_volatility": float(inf_vol_stab),
            "recession_count": int(rec_count_stab),
            "recession_duration": int(rec_dur_stab)
        }
    }

def plot_comparisons(baseline: SimulationResults, stabilized: SimulationResults):
    os.makedirs("reports", exist_ok=True)

    # GDP
    plt.figure(figsize=(10, 6))
    plt.plot(baseline.gdp, label="Baseline (No Stabilizers)", alpha=0.7)
    plt.plot(stabilized.gdp, label="Stabilized", alpha=0.7)
    plt.title("GDP Comparison")
    plt.xlabel("Tick")
    plt.ylabel("GDP")
    plt.legend()
    plt.savefig("reports/gdp_comparison.png")
    plt.close()

    # Inflation
    plt.figure(figsize=(10, 6))
    plt.plot(baseline.inflation, label="Baseline (No Stabilizers)", alpha=0.7)
    plt.plot(stabilized.inflation, label="Stabilized", alpha=0.7)
    plt.title("Price Level Comparison")
    plt.xlabel("Tick")
    plt.ylabel("Avg Price")
    plt.legend()
    plt.savefig("reports/inflation_stability.png")
    plt.close()

    # GDP Volatility Rolling Window
    def rolling_std(series, window=50):
        if not series: return []
        # Calculate rolling std of growth rate
        arr = np.array(series)
        growth = np.diff(arr) / np.where(arr[:-1]==0, 1, arr[:-1])
        # Pad beginning
        growth = np.insert(growth, 0, 0)

        result = []
        for i in range(len(growth)):
            start = max(0, i-window)
            window_slice = growth[start:i+1]
            result.append(np.std(window_slice))
        return result

    vol_base = rolling_std(baseline.gdp)
    vol_stab = rolling_std(stabilized.gdp)

    plt.figure(figsize=(10, 6))
    plt.plot(vol_base, label="Baseline Volatility", alpha=0.7)
    plt.plot(vol_stab, label="Stabilized Volatility", alpha=0.7)
    plt.title("GDP Growth Volatility (Rolling 50 ticks)")
    plt.xlabel("Tick")
    plt.ylabel("Std Dev")
    plt.legend()
    plt.savefig("reports/gdp_volatility.png")
    plt.close()

def main():
    print("🚀 Starting Soft Landing Verification...")

    # Run Baseline
    baseline_results = run_verification_simulation(enable_stabilizers=False)
    # Serialize dataclass to dict
    with open("reports/soft_landing_baseline.json", "w") as f:
        json.dump(baseline_results.__dict__, f)

    # Run Stabilized
    stabilized_results = run_verification_simulation(enable_stabilizers=True)
    with open("reports/soft_landing_stabilized.json", "w") as f:
        json.dump(stabilized_results.__dict__, f)

    # Analyze
    metrics = analyze_results(baseline_results, stabilized_results)

    # Plot
    plot_comparisons(baseline_results, stabilized_results)

    print("\n✅ Verification Complete.")
    print("📊 Summary:")
    print(json.dumps(metrics, indent=2))

    # Check for success criteria
    if metrics["stabilized"]["gdp_volatility"] <= metrics["baseline"]["gdp_volatility"]:
        print("✅ SUCCESS: Stabilizers reduced or maintained GDP volatility.")
    else:
        print("⚠️ WARNING: Stabilizers did not reduce GDP volatility. (This might happen in short runs or specific seeds)")

if __name__ == "__main__":
    main()
