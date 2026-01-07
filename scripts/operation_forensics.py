import logging
import sys
import os
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Ensure simulation package is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import create_simulation
from utils.logging_manager import setup_logging
import config

# --- Forensic Log Handler ---
class ForensicLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.death_records: List[Dict[str, Any]] = []

    def emit(self, record):
        if hasattr(record, "agent_id") and hasattr(record, "cause") and record.cause == "starvation":
             # This matches our AGENT_DEATH log
             if hasattr(record, "food_inventory"): # Check for forensic fields
                 data = {
                     "tick": record.tick,
                     "agent_id": record.agent_id,
                     "cash_at_death": getattr(record, "cash_at_death", 0.0),
                     "food_inventory": getattr(record, "food_inventory", 0.0),
                     "market_food_price": getattr(record, "market_food_price", None),
                     "last_labor_offer_tick": getattr(record, "last_labor_offer_tick", 0),
                     "job_vacancies_available": getattr(record, "job_vacancies_available", 0)
                 }
                 self.death_records.append(data)

def run_forensic_investigation():
    # 1. Setup Logging
    # Ensure standard logging is setup FIRST so it doesn't overwrite our handler
    setup_logging()

    # We'll use our custom handler to capture death events
    forensic_handler = ForensicLogHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(forensic_handler)

    # [Fix] Attach to specific loggers to bypass propagation issues
    logging.getLogger("simulation").addHandler(forensic_handler)
    logging.getLogger("main").addHandler(forensic_handler)

    # 2. Run Simulation (STRESS TEST MODE)
    print("Initializing Operation Forensics Simulation (STRESS TEST: Asset=50.0)...")
    
    # [CRITICAL] Runtime Config Override for Stress Test
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 10.0
    config.INITIAL_FIRM_CAPITAL_MEAN = 100.0
    config.INITIAL_FIRM_INVENTORY_MEAN = 0.0
    config.GOVERNMENT_STIMULUS_ENABLED = False
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 5.0
    config.GOODS['basic_food']['utility_effects']['survival'] = 1
    config.FIRM_PRODUCTIVITY_FACTOR = 1.0
    
    sim = create_simulation()

    try:
        for i in range(200):
            sim.run_tick()
            if (i+1) % 50 == 0:
                print(f"Tick {i+1}/200 complete...")
    except Exception as e:
        print(f"Simulation crashed at tick {sim.time}: {e}")
        import traceback
        traceback.print_exc()

    # 3. Analyze Results
    # Deduplicate records (tick, agent_id)
    unique_deaths = {}
    for record in forensic_handler.death_records:
        key = (record["tick"], record["agent_id"])
        if key not in unique_deaths:
            unique_deaths[key] = record

    deduplicated_records = list(unique_deaths.values())
    print(f"\nSimulation Complete. Analyzing {len(deduplicated_records)} deaths (deduplicated)...")

    type_a_count = 0
    type_b_count = 0
    type_c_count = 0
    type_d_count = 0

    report_lines = []
    report_lines.append("# AUTOPSY REPORT: FORENSIC ANALYSIS")
    report_lines.append(f"**Total Deaths**: {len(deduplicated_records)}")
    report_lines.append("")

    sample_cases = []

    for record in deduplicated_records:
        death_tick = record["tick"]
        vacancies = record["job_vacancies_available"]
        last_offer = record["last_labor_offer_tick"]
        cash = record["cash_at_death"]
        price = record["market_food_price"]
        inventory = record["food_inventory"]

        # Classification Logic (Priority: A -> B -> C)
        # Type A: Job Vacancy = 0
        # Type B: Last Labor Offer > 10 ticks ago (or never)
        # Type C: Cash > Price (Won't Eat)

        is_type_a = vacancies == 0
        is_type_b = (death_tick - last_offer) > 10
        
        price_val = price if price is not None else 999999.0
        is_type_c = (cash >= price_val)
        is_type_d = (cash < price_val)

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
            sample_cases.append(f"- **{assigned_type}** | Agent #{record['agent_id']} | Tick: {death_tick} | Cash: {cash:.2f} | Vacancies: {vacancies} | Last Offer: {last_offer} | Price: {price}")

    total = len(deduplicated_records)
    if total > 0:
        report_lines.append("## Classification Summary")
        report_lines.append(f"- **Type A (No Jobs)**: {type_a_count} ({type_a_count/total:.1%})")
        report_lines.append(f"- **Type B (Won't Work)**: {type_b_count} ({type_b_count/total:.1%})")
        report_lines.append(f"- **Type C (Won't Eat)**: {type_c_count} ({type_c_count/total:.1%})")
        report_lines.append(f"- **Type D (Poverty)**: {type_d_count} ({type_d_count/total:.1%})")
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
