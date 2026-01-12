import sys
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt

# Ensure simulation package is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from main import create_simulation
from utils.logging_manager import setup_logging
import config
from config import EngineType

def run_malthusian_experiment():
    # 1. Setup Logging
    setup_logging()
    logger = logging.getLogger("malthusian_experiment")

    # 2. Configure Overrides (Malthusian Trap)
    overrides = {
        "CAPITAL_DEPRECIATION_RATE": 0.0,
        "INITIAL_FIRM_CAPITAL_MEAN": 50.0,
        "FIRM_PRODUCTIVITY_FACTOR": 1.0,
        "BIOLOGICAL_FERTILITY_RATE": 0.2,
        "UNEMPLOYMENT_BENEFIT_RATIO": 0.0,
        "GOVERNMENT_STIMULUS_ENABLED": False,
        "NUM_HOUSEHOLDS": 20, # Start small to allow growth
        "SIMULATION_TICKS": 1000,
        "DEFAULT_ENGINE_TYPE": EngineType.AI_DRIVEN
    }

    print("Initializing Malthusian Trap Experiment...")
    print(f"Configuration: {overrides}")

    # 3. Initialize Simulation
    sim = create_simulation(overrides=overrides)

    # Data Collection
    history = []

    # 4. Simulation Loop
    try:
        for tick in range(1, 1001):
            # Force System 1 Reproduction (Instinctual)
            for agent in sim.households:
                if hasattr(agent, "decision_engine"):
                     agent.decision_engine.reproduction_mode = 'SYSTEM1'

            sim.run_tick()

            # Metric Collection
            pop_count = len(sim.households)

            # Calculate Mean Wage
            employed_agents = [h for h in sim.households if h.is_employed]
            mean_wage = sum(h.current_wage for h in employed_agents) / len(employed_agents) if employed_agents else 0.0

            # Calculate Survival Cost (Average cost of 1 unit of food * monthly need, approx)
            # Or use the agent's tracked survival cost if available.
            # Proxy: config.GOODS['basic_food']['initial_price'] * consumption
            # Better: Average price of food in market
            food_market = sim.markets.get("basic_food")
            food_price = 5.0
            if food_market and hasattr(food_market, "get_daily_avg_price"):
                 avg = food_market.get_daily_avg_price()
                 if avg > 0:
                     food_price = avg

            survival_cost = food_price * config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK

            # Death Count (Starvation)
            # Attribution needs to come from Repository or log parsing.
            # For this script, we can track population delta + births.
            # But specific starvation count is harder without accessing the repo's attrition method.
            # We will use the repo method if available.

            # Get attrition from repository
            # get_attrition_counts requires (start_tick, end_tick, run_id)
            # We check just this tick (tick, tick)
            attrition = sim.repository.get_attrition_counts(tick, tick, sim.run_id)
            starvation_deaths = attrition.get("death_count", 0)

            history.append({
                "tick": tick,
                "population": pop_count,
                "mean_wage": mean_wage,
                "survival_cost": survival_cost,
                "starvation_deaths": starvation_deaths,
                "food_price": food_price
            })

            if tick % 50 == 0:
                print(f"Tick {tick}: Pop={pop_count}, Wage={mean_wage:.2f}, Cost={survival_cost:.2f}, Deaths={starvation_deaths}")

    except Exception as e:
        logger.error(f"Simulation crashed at tick {sim.time}: {e}", exc_info=True)
        print(f"CRASH: {e}")

    # 5. Analysis & Reporting
    df = pd.DataFrame(history)

    # Save Raw Data
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/malthusian_data.csv", index=False)

    # Detect Iron Ceiling
    # Definition: Point where Wage < Survival Cost AND Population stabilizes/declines

    # Filter ticks where Wage < Survival Cost
    trap_zone = df[df["mean_wage"] < df["survival_cost"]]

    iron_ceiling_tick = None
    iron_ceiling_pop = 0
    iron_ceiling_wage = 0

    if not trap_zone.empty:
        # Find the point of max population within or near the trap zone
        max_pop_idx = trap_zone["population"].idxmax()
        iron_ceiling_tick = trap_zone.loc[max_pop_idx, "tick"]
        iron_ceiling_pop = trap_zone.loc[max_pop_idx, "population"]
        iron_ceiling_wage = trap_zone.loc[max_pop_idx, "mean_wage"]

        print(f"\n[IRON CEILING DETECTED]")
        print(f"Tick: {iron_ceiling_tick}")
        print(f"Population Peak: {iron_ceiling_pop}")
        print(f"Wage at Peak: {iron_ceiling_wage:.2f}")
    else:
        print("\n[NO IRON CEILING DETECTED] Wages remained above survival cost or population kept growing.")

    # Calculate Metric: Population Doubling vs Real Wage Drop
    # Real Wage = Mean Wage / Survival Cost
    df["real_wage"] = df.apply(lambda row: row["mean_wage"] / row["survival_cost"] if row["survival_cost"] > 0 else 0, axis=1)

    # Find start and end points for doubling (e.g., Start Pop -> 2 * Start Pop)
    start_pop = df.iloc[0]["population"]
    target_pop = start_pop * 2

    doubling_rows = df[df["population"] >= target_pop]

    metric_text = "N/A (Population did not double)"
    if not doubling_rows.empty:
        double_idx = doubling_rows.index[0]
        start_real_wage = df.iloc[0]["real_wage"]
        end_real_wage = df.iloc[double_idx]["real_wage"]

        pct_change = ((end_real_wage - start_real_wage) / start_real_wage) * 100
        metric_text = f"{pct_change:.2f}% (Pop {start_pop} -> {df.iloc[double_idx]['population']})"
        print(f"Real Wage Change on Doubling: {metric_text}")

    # Write Report
    report_content = [
        "# 🏛️ Malthusian Trap Experiment Report",
        "",
        "## 1. Configuration",
        f"- **Initial Capital**: {overrides['INITIAL_FIRM_CAPITAL_MEAN']}",
        f"- **Productivity**: {overrides['FIRM_PRODUCTIVITY_FACTOR']}",
        f"- **Depreciation**: {overrides['CAPITAL_DEPRECIATION_RATE']}",
        f"- **Fertility**: {overrides['BIOLOGICAL_FERTILITY_RATE']}",
        "",
        "## 2. Iron Ceiling Analysis",
        f"- **Detected Tick**: {iron_ceiling_tick if iron_ceiling_tick else 'None'}",
        f"- **Population Limit**: {iron_ceiling_pop}",
        f"- **Wage at Ceiling**: {iron_ceiling_wage:.2f}",
        "",
        "## 3. Correlation Metric",
        f"- **Real Wage Change (Pop 2x)**: {metric_text}",
        "",
        "## 4. Time Series Data (Sample)",
        "| Tick | Pop | Wage | Cost | Deaths | Real Wage |",
        "|---|---|---|---|---|---|",
    ]

    # Add sample rows (every 100 ticks)
    for i in range(0, len(df), 100):
        row = df.iloc[i]
        report_content.append(f"| {row['tick']} | {row['population']} | {row['mean_wage']:.2f} | {row['survival_cost']:.2f} | {row['starvation_deaths']} | {row['real_wage']:.2f} |")

    os.makedirs("reports", exist_ok=True)
    with open("reports/malthusian_trap_report.md", "w") as f:
        f.write("\n".join(report_content))

    print("Report generated: reports/malthusian_trap_report.md")

if __name__ == "__main__":
    run_malthusian_experiment()
