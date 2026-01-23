import logging
import sys
from pathlib import Path
import os
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Ensure simulation package is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from utils.logging_manager import setup_logging
import config


# --- Forensic Log Handler ---
class ForensicLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.death_records: List[Dict[str, Any]] = []
        self.stimulus_records: List[Dict[str, Any]] = []
        self.all_records: List[Dict[str, Any]] = []

    def emit(self, record):
        # Capture for verify_genesis generic access
        self.all_records.append(record.__dict__)

        # Specific capturing for forensics
        if (
            hasattr(record, "agent_id")
            and hasattr(record, "cause")
            and record.cause == "starvation"
        ):
            if hasattr(record, "food_inventory"):  # Check for forensic fields
                data = {
                    "tick": getattr(record, "tick", 0),
                    "agent_id": record.agent_id,
                    "cash_at_death": getattr(record, "cash_at_death", 0.0),
                    "food_inventory": getattr(record, "food_inventory", 0.0),
                    "market_food_price": getattr(record, "market_food_price", None),
                    "last_labor_offer_tick": getattr(
                        record, "last_labor_offer_tick", 0
                    ),
                    "job_vacancies_available": getattr(
                        record, "job_vacancies_available", 0
                    ),
                }
                self.death_records.append(data)

        if "STIMULUS_TRIGGERED" in record.getMessage():
            self.stimulus_records.append(
                {"tick": getattr(record, "tick", 0), "message": record.getMessage()}
            )


def run_forensic_investigation():
    # 1. Setup Logging
    # [FIX: WO-Diag-003] setup_logging first to avoid clearing handlers
    setup_logging()

    forensic_handler = ForensicLogHandler()
    # Attach to root and simulation loggers explicitly due to propagate=False
    logging.getLogger().addHandler(forensic_handler)
    logging.getLogger("simulation").addHandler(forensic_handler)
    logging.getLogger("main").addHandler(forensic_handler)

    # 2. Run Simulation (STRESS TEST MODE)
    print("Initializing Operation Forensics Simulation (STRESS TEST: Asset=50.0)...")

    # [CRITICAL] Runtime Config Override for Stress Test
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 50.0

    sim = create_simulation()

    try:
        for i in range(500):
            sim.run_tick()
            if (i + 1) % 50 == 0:
                print(f"Tick {i + 1}/500 complete...")
    except Exception as e:
        print(f"Simulation crashed at tick {sim.time}: {e}")
        import traceback

        traceback.print_exc()

    # 3. Analyze Results
    print(
        f"\nSimulation Complete. Analyzing {len(forensic_handler.death_records)} deaths..."
    )

    type_a_count = 0
    type_b_count = 0
    type_c_count = 0
    type_d_count = 0
    report_lines = []
    sample_cases = []

    seen_deaths = set()
    unique_deaths = []
    for record in forensic_handler.death_records:
        death_key = (record["tick"], record["agent_id"])
        if death_key not in seen_deaths:
            seen_deaths.add(death_key)
            unique_deaths.append(record)

    for record in unique_deaths:
        death_tick = record["tick"]
        vacancies = record["job_vacancies_available"]
        last_offer = record["last_labor_offer_tick"]
        cash = record["cash_at_death"]
        price = record["market_food_price"]
        inventory = record["food_inventory"]

        # Classification Logic (Priority: A -> B -> C -> D)
        is_type_a = vacancies == 0
        is_type_b = (death_tick - last_offer) > 10

        price_val = price if price is not None else 999999.0
        is_type_c = cash >= price_val
        is_type_d = cash < price_val

        assigned_type = "Unknown"

        if is_type_a:
            type_a_count += 1
            assigned_type = "Type A (No Jobs)"
        elif is_type_b:
            type_b_count += 1
            assigned_type = "Type B (Won't Work)"
        elif is_type_c:
            type_c_count += 1
            assigned_type = "Type C (Won't Eat)"
        elif is_type_d:
            type_d_count += 1
            assigned_type = "Type D (Poverty)"
        else:
            assigned_type = "Unclassified"

        # Collect sample cases (first 5 of each type)
        if len(sample_cases) < 15:
            sample_cases.append(
                f"- **{assigned_type}** | Agent #{record['agent_id']} | Tick: {death_tick} | Cash: {cash:.2f} | Vacancies: {vacancies} | Last Offer: {last_offer} | Price: {price}"
            )

    total = len(unique_deaths)
    if total > 0:
        report_lines.append("## Classification Summary")
        report_lines.append(
            f"- **Type A (No Jobs)**: {type_a_count} ({type_a_count / total:.1%})"
        )
        report_lines.append(
            f"- **Type B (Won't Work)**: {type_b_count} ({type_b_count / total:.1%})"
        )
        report_lines.append(
            f"- **Type C (Won't Eat)**: {type_c_count} ({type_c_count / total:.1%})"
        )
        report_lines.append(
            f"- **Type D (Poverty)**: {type_d_count} ({type_d_count / total:.1%})"
        )
    else:
        report_lines.append("## Classification Summary")
        report_lines.append("- No deaths recorded.")

    report_lines.append("")
    report_lines.append("## Sample Cases")
    for case in sample_cases:
        report_lines.append(case)

    # 4. Write Report
    os.makedirs("reports", exist_ok=True)
    with open("reports/AUTOPSY_REPORT.md", "w") as f:
        f.write("\n".join(report_lines))

    print("\n".join(report_lines))
    print(f"\nReport saved to reports/AUTOPSY_REPORT.md")


if __name__ == "__main__":
    run_forensic_investigation()
