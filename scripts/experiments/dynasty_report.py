
import sys
import os
import logging
import numpy as np
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from simulation.engine import Simulation
from simulation.core_agents import Household
import config
from main import create_simulation

# Setup logging
logging.basicConfig(level=logging.WARNING) # Optimize: ERROR/WARNING only
logger = logging.getLogger("dynasty_report")
logger.setLevel(logging.INFO)

def run_dynasty_experiment():
    print("--- Starting Dynasty Report Experiment (WO-052) ---")

    # Configuration Overrides for Stability (Lively God Mode - v2)
    overrides = {
        "NUM_HOUSEHOLDS": 100,
        "WAGE_DECAY_RATE": 0.001,
        "RESERVATION_WAGE_FLOOR": 0.1,
        "FIRM_MAINTENANCE_FEE": 0.0,

        # Immortality (Prevent Death)
        "SURVIVAL_NEED_DEATH_THRESHOLD": 99999.0,
        "HOUSEHOLD_DEATH_TURNS_THRESHOLD": 99999,
        "ASSETS_DEATH_THRESHOLD": -99999.0,

        # Active Demand (Encourage Consumption & Work)
        "MASLOW_SURVIVAL_THRESHOLD": 30.0, # Panic earlier to find work
        "SURVIVAL_NEED_CONSUMPTION_THRESHOLD": 30.0, # Start eating earlier
        "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK": 2.0, # Normal consumption
        "BASE_DESIRE_GROWTH": 1.0, # Needs grow -> Hunger -> Demand

        # Safety Net (Reduce to 30% of survival cost)
        "UNEMPLOYMENT_BENEFIT_RATIO": 0.3,

        # Initial State
        "INITIAL_FIRM_CAPITAL_MEAN": 500000.0, # Correct Key
        "GOVERNMENT_STIMULUS_ENABLED": True,
        "TAX_MODE": "FLAT",
        "BASE_INCOME_TAX_RATE": 0.0 # No tax to keep money in pockets
    }

    simulation = create_simulation(overrides)

    # [OPTIMIZATION] Mute simulation logs to speed up execution
    logging.getLogger("simulation").setLevel(logging.WARNING)
    logging.getLogger("main").setLevel(logging.WARNING)

    # [HOTFIX] Inject Infinite Government Funding for Welfare
    simulation.government.assets = 100000000.0

    # Run 1000 Ticks
    TARGET_TICKS = 1000
    for tick in range(TARGET_TICKS):
        simulation.run_tick()

        active_agents = len([h for h in simulation.households if h.is_active])
        if active_agents < 5:
            print(f"CRITICAL: Population collapsed to {active_agents} at tick {tick}. Aborting.")
            break

        if tick % 100 == 0:
            print(f"Tick {tick}: Active Agents = {active_agents}, GDP = {simulation.tracker.get_latest_indicators().get('total_production', 0):.2f}")

    # Record Final Wealth for Survivors
    print("\n--- Simulation Completed. Recording Final Wealth ---")
    survivors = [h for h in simulation.households if h.is_active]
    for agent in survivors:
        simulation.mobility_tracker.record_final_wealth(agent.id, agent.assets)

    # Metrics
    survival_count = len(survivors)
    ige = simulation.mobility_tracker.calculate_ige()
    r_squared = simulation.mobility_tracker.calculate_r_squared()

    # Generational Distribution
    generations = [h.generation for h in survivors]
    gen_dist = dict(Counter(generations))

    # Verdict
    verdict = "Unknown"
    if ige < 0.2: verdict = "Meritocracy"
    elif ige < 0.6: verdict = "Status Quo"
    else: verdict = "Caste System"

    # Generate ASCII Scatter Plot
    plot_str = generate_ascii_plot(simulation.mobility_tracker)

    # Generate Report Content
    report_content = f"""# Dynasty Report (WO-052)
**Date:** 2026-01-12
**Simulation Ticks:** {simulation.time}
**Population:** {survival_count}/{overrides['NUM_HOUSEHOLDS']} (Start)

## 1. Survival Rate & Demographics
- **Final Population:** {survival_count}
- **Survival Rate:** {survival_count / overrides['NUM_HOUSEHOLDS'] * 100:.1f}%
- **Generational Distribution:**
"""
    for gen, count in sorted(gen_dist.items()):
        report_content += f"  - Generation {gen}: {count} agents\n"

    report_content += f"""
## 2. IGE Metric (Intergenerational Mobility)
- **IGE (Beta):** {ige:.4f}
- **R-squared ($R^2$):** {r_squared:.4f}

## 3. The Verdict
**{verdict}**
*(Thresholds: Meritocracy < 0.2, Status Quo < 0.6, Caste System >= 0.6)*

## 4. Wealth Mobility Scatter Plot
Log-Log Plot of Parent Wealth (X) vs Child Wealth (Y).
```
{plot_str}
```
"""

    # Write to File
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/dynasty_report_20260112.md"
    with open(report_path, "w") as f:
        f.write(report_content)

    print(f"Report generated at: {report_path}")
    print(report_content)


def generate_ascii_plot(tracker):
    data_points = []
    for r in tracker.records.values():
        if r.is_complete and r.parent_wealth > 0 and r.child_wealth > 0:
            x = np.log(r.parent_wealth + 1)
            y = np.log(r.child_wealth + 1)
            data_points.append((x, y))

    if not data_points:
        return "Not enough data for scatter plot."

    xs, ys = zip(*data_points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = 60
    height = 20
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for x, y in data_points:
        if max_x == min_x: x_norm = 0.5
        else: x_norm = (x - min_x) / (max_x - min_x)

        if max_y == min_y: y_norm = 0.5
        else: y_norm = (y - min_y) / (max_y - min_y)

        col = int(x_norm * (width - 1))
        row = int((1 - y_norm) * (height - 1))
        grid[row][col] = '*'

    output = []
    output.append(f"{max_y:.1f} ^")
    for row in grid:
        output.append("    | " + "".join(row))
    output.append(f"{min_y:.1f} +-" + "-"*width + ">")
    output.append(f"      {min_x:.1f}" + " "*(width-10) + f"{max_x:.1f}")
    output.append("      (Parent Wealth ->)")

    return "\n".join(output)

if __name__ == "__main__":
    run_dynasty_experiment()
