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
    # We'll use our custom handler to capture death events
    forensic_handler = ForensicLogHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(forensic_handler)
    # Ensure standard logging is also setup (so we don't miss other errors)
    setup_logging()

    # 2. Run Simulation
    print("Initializing Operation Forensics Simulation (100 Ticks)...")
    sim = create_simulation()

    try:
        for i in range(100):
            sim.run_tick()
            if (i+1) % 10 == 0:
                print(f"Tick {i+1}/100 complete...")
    except Exception as e:
        print(f"Simulation crashed at tick {sim.time}: {e}")
        import traceback
        traceback.print_exc()

    # 3. Analyze Results
    print(f"\nSimulation Complete. Analyzing {len(forensic_handler.death_records)} deaths...")

    type_a_count = 0
    type_b_count = 0
    type_c_count = 0

    report_lines = []
    report_lines.append("=== FORENSIC REPORT ===")
    report_lines.append(f"Total Deaths: {len(forensic_handler.death_records)}")

    sample_cases = []

    for record in forensic_handler.death_records:
        death_tick = record["tick"]
        vacancies = record["job_vacancies_available"]
        last_offer = record["last_labor_offer_tick"]
        cash = record["cash_at_death"]
        price = record["market_food_price"]
        inventory = record["food_inventory"]

        # Classification Logic (Priority: A -> B -> C)
        # Based on WO-021:
        # Type A: Job Vacancy = 0
        # Type B: Last Labor Offer > 10 ticks ago (or never)
        # Type C: Cash > Price (Won't Eat)

        is_type_a = vacancies == 0

        # Type B: "Labor Offer count = 0 in last 10 ticks" -> (current_tick - last_offer > 10)
        # Note: If never offered, last_offer is 0.
        is_type_b = (death_tick - last_offer) > 10

        # Type C: Cash > Price (if Price is known) and Inventory empty
        # Note: inventory is checked at death, usually 0 if starvation.
        # If price is None (no market data), we can't strictly classify as C based on price,
        # but usually it means market collapse or no sellers.
        price_val = price if price is not None else 999999.0
        is_type_c = (cash >= price_val)

        assigned_type = "Unknown"

        if is_type_a:
            type_a_count += 1
            assigned_type = "Type A"
        elif is_type_b:
            type_b_count += 1
            assigned_type = "Type B"
        elif is_type_c:
            type_c_count += 1
            assigned_type = "Type C"
        else:
            # Fallback or mixed causes
            assigned_type = "Unclassified"

        # Collect sample cases (first 2 of each type)
        if len(sample_cases) < 10: # Just collect some
            sample_cases.append(f"[{assigned_type}] Agent #{record['agent_id']}: Cash={cash:.2f}, Vacancies={vacancies}, LastOffer={last_offer} (Tick {death_tick}), Price={price}")

    total = len(forensic_handler.death_records)
    if total > 0:
        report_lines.append(f"- Type A (No Jobs): {type_a_count} ({type_a_count/total:.1%})")
        report_lines.append(f"- Type B (Won't Work): {type_b_count} ({type_b_count/total:.1%})")
        report_lines.append(f"- Type C (Won't Eat): {type_c_count} ({type_c_count/total:.1%})")
    else:
        report_lines.append("- Type A (No Jobs): 0 (0%)")
        report_lines.append("- Type B (Won't Work): 0 (0%)")
        report_lines.append("- Type C (Won't Eat): 0 (0%)")

    report_lines.append("\nSample Cases:")
    for case in sample_cases:
        report_lines.append(case)

    # 4. Write Report
    os.makedirs("reports", exist_ok=True)
    with open("reports/forensic_report.txt", "w") as f:
        f.write("\n".join(report_lines))

    print("\n".join(report_lines))
    print(f"\nReport saved to reports/forensic_report.txt")

if __name__ == "__main__":
    run_forensic_investigation()
