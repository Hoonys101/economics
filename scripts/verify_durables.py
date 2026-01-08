
import sys
import os
import logging
from typing import List, Dict, Any

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from main import create_simulation
from simulation.core_agents import Household

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_durables")

def generate_ascii_chart(data: List[float], title: str, max_width: int = 50) -> str:
    if not data:
        return "No Data"

    min_val = min(data)
    max_val = max(data)
    if max_val == min_val:
        normalized = [0 for _ in data]
    else:
        normalized = [int((x - min_val) / (max_val - min_val) * max_width) for x in data]

    lines = [f"### {title}"]
    lines.append(f"Range: {min_val:.2f} - {max_val:.2f}")
    lines.append("```")
    for i, (val, norm_val) in enumerate(zip(data, normalized)):
        bar = "*" * norm_val
        lines.append(f"T{i:03d} | {bar} ({val:.2f})")
    lines.append("```")
    return "\n".join(lines)

def run_verification():
    logger.info("Starting Durables Business Cycle Verification...")

    # 1. Configuration Overrides
    overrides = {
        "NUM_HOUSEHOLDS": 50,
        "NUM_FIRMS": 6,
        "FIRM_SPECIALIZATIONS": {
            0: "basic_food",
            1: "basic_food",
            2: "clothing",
            3: "clothing",
            4: "consumer_goods",
            5: "consumer_goods",
        },
        "SIMULATION_TICKS": 100,
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": 10000.0,
        "GOVERNMENT_STIMULUS_ENABLED": True,
        "INITIAL_FIRM_INVENTORY_MEAN": 0.0,
        "FIRM_MIN_PRODUCTION_TARGET": 50.0,

        # Prevent initial panic selling by firms (Give them runway)
        "INITIAL_FIRM_CAPITAL_MEAN": 50000.0,

        # Prevent hoarding by households (Don't buy if need is low)
        "NEED_FACTOR_BASE": 0.1,

        # Force immediate consumption (installation) of durables
        "INITIAL_HOUSEHOLD_NEEDS_MEAN": {
            "survival": 60.0,
            "asset": 10.0,
            "social": 20.0,
            "improvement": 10.0,
            "quality": 90.0, # High initial need -> Buy & Install immediately
            "liquidity_need": 50.0,
            # Legacy Keys
            "survival_need": 60.0,
            "recognition_need": 20.0,
            "growth_need": 10.0,
            "wealth_need": 10.0,
            "imitation_need": 15.0,
            "labor_need": 0.0,
            "child_rearing_need": 0.0
        },
        "NEED_MEDIUM_THRESHOLD": 10.0,
    }

    # 2. Initialize Simulation
    sim = create_simulation(overrides=overrides)

    sales_volume_history: List[float] = []
    avg_wealth_history: List[float] = []

    logger.info(f"Simulation initialized. Ticks: {sim.config_module.SIMULATION_TICKS}")

    # 3. Loop
    for tick in range(sim.config_module.SIMULATION_TICKS):
        try:
            sim.run_tick()
        except Exception as e:
            logger.error(f"Simulation crashed at tick {tick}: {e}")
            raise e

        # Metric 1: Sales Volume
        market = sim.markets.get("consumer_goods")
        daily_vol = 0.0
        daily_price = 15.0 # Default

        if market:
            daily_vol = market.get_daily_volume()
            p = market.get_daily_avg_price()
            if p > 0:
                daily_price = p

        sales_volume_history.append(daily_vol)

        # Metric 2: Wealth Storage
        total_wealth = 0.0
        active_count = 0
        total_inventory_goods = 0
        total_durable_count = 0

        for h in sim.households:
            if not h.is_active:
                continue

            cash = h.assets
            durable_value = 0.0

            # Debug Inventory vs Durable Assets
            total_inventory_goods += h.inventory.get("consumer_goods", 0)

            # Calculate Durable Value
            for asset in h.durable_assets:
                if asset["item_id"] == "consumer_goods":
                    total_durable_count += 1
                    quality = asset["quality"]
                    remaining = asset["remaining_life"]
                    base_life = 50.0
                    price = daily_price
                    durable_value += quality * (remaining / base_life) * price

            total_wealth += (cash + durable_value)
            active_count += 1

        avg_wealth = total_wealth / active_count if active_count > 0 else 0.0
        avg_wealth_history.append(avg_wealth)

        if tick % 10 == 0:
            logger.info(f"Tick {tick}: Vol={daily_vol:.1f}, AvgWealth={avg_wealth:.1f}, InvGoods={total_inventory_goods:.1f}, Installed={total_durable_count}")

    # 4. Post-Simulation Analysis (Metric 3: Quality Segmentation)
    logger.info("Calculating Quality Segmentation...")

    # Re-calculate wealth for final snapshot sorting
    household_wealth_map = []

    market = sim.markets.get("consumer_goods")
    final_price = market.get_daily_avg_price() if market else 15.0
    if final_price <= 0: final_price = 15.0

    for h in sim.households:
        if not h.is_active:
            continue

        cash = h.assets
        durable_val = 0.0
        owned_durables = [a for a in h.durable_assets if a["item_id"] == "consumer_goods"]

        for asset in owned_durables:
            q = asset["quality"]
            rem = asset["remaining_life"]
            durable_val += q * (rem / 50.0) * final_price

        total = cash + durable_val

        # Calculate Avg Quality for this household
        avg_q = 0.0
        if owned_durables:
            avg_q = sum(a["quality"] for a in owned_durables) / len(owned_durables)

        household_wealth_map.append({
            "id": h.id,
            "wealth": total,
            "avg_quality": avg_q,
            "owned_count": len(owned_durables)
        })

    # Sort by wealth descending
    household_wealth_map.sort(key=lambda x: x["wealth"], reverse=True)

    count = len(household_wealth_map)
    top_10_idx = max(1, int(count * 0.1))
    bottom_10_idx = max(1, int(count * 0.1))

    top_10 = household_wealth_map[:top_10_idx]
    bottom_10 = household_wealth_map[-bottom_10_idx:]

    avg_q_top = sum(x["avg_quality"] for x in top_10) / len(top_10) if top_10 else 0.0
    avg_q_bottom = sum(x["avg_quality"] for x in bottom_10) / len(bottom_10) if bottom_10 else 0.0

    logger.info(f"Top 10% Avg Quality: {avg_q_top:.2f}")
    logger.info(f"Bottom 10% Avg Quality: {avg_q_bottom:.2f}")

    # 5. Generate Report
    report_content = [
        "# Durables Business Cycle Verification Report",
        "",
        "## 1. The Cliff & Echo (Sales Volume)",
        generate_ascii_chart(sales_volume_history, "Consumer Goods Sales Volume"),
        "",
        "## 2. Wealth Storage (Asset Accumulation)",
        generate_ascii_chart(avg_wealth_history, "Avg Household Wealth (Cash + Durable Value)"),
        "",
        "## 3. Quality Segmentation (at T=100)",
        "| Group | Avg Quality | Avg Wealth | Owned Count (Avg) |",
        "|---|---|---|---|",
        f"| Top 10% | {avg_q_top:.2f} | {sum(x['wealth'] for x in top_10)/len(top_10):.1f} | {sum(x['owned_count'] for x in top_10)/len(top_10):.1f} |",
        f"| Bottom 10% | {avg_q_bottom:.2f} | {sum(x['wealth'] for x in bottom_10)/len(bottom_10):.1f} | {sum(x['owned_count'] for x in bottom_10)/len(bottom_10):.1f} |",
        "",
        "## Analysis",
        "- **Cliff & Echo**: Check T=0-10 for spike and ~T=50 for echo.",
        "- **Wealth**: Check for sawtooth pattern.",
        "- **Quality**: Check if Top 10% > Bottom 10% (Expect > 1.0 for rich).",
        ""
    ]

    os.makedirs("reports", exist_ok=True)
    with open("reports/DURABLES_CYCLE_REPORT.md", "w") as f:
        f.write("\n".join(report_content))

    logger.info("Report generated at reports/DURABLES_CYCLE_REPORT.md")

if __name__ == "__main__":
    run_verification()
