import logging
import sys
import argparse
import csv
from pathlib import Path
import os
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Ensure simulation package is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from modules.common.utils.logging_manager import setup_logging
import config

# --- Forensic Log Handler ---
class ForensicLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.death_records: List[Dict[str, Any]] = []
        self.stimulus_records: List[Dict[str, Any]] = []
        self.all_records: List[Dict[str, Any]] = []

    def emit(self, record):
        # Capture raw attributes for refined analysis
        data = record.__dict__.copy()
        # Remove non-serializable objects if necessary
        if "exc_info" in data: data["exc_info"] = None
        self.all_records.append(data)

        # Specific capturing for forensics
        if hasattr(record, "agent_id") and hasattr(record, "cause") and record.cause == "starvation":
             if hasattr(record, "food_inventory"): # Check for forensic fields
                 death_data = {
                     "tick": getattr(record, "tick", 0),
                     "agent_id": record.agent_id,
                     "cash_at_death": getattr(record, "cash_at_death", 0.0),
                     "food_inventory": getattr(record, "food_inventory", 0.0),
                     "market_food_price": getattr(record, "market_food_price", None),
                     "last_labor_offer_tick": getattr(record, "last_labor_offer_tick", 0),
                     "job_vacancies_available": getattr(record, "job_vacancies_available", 0)
                 }
                 self.death_records.append(death_data)
        
        if "STIMULUS_TRIGGERED" in record.getMessage():
             self.stimulus_records.append({
                 "tick": getattr(record, "tick", 0),
                 "message": record.getMessage()
             })

def run_forensic_investigation(ticks=50, stress_test=True, output_log=None):
    # 1. Setup Logging
    setup_logging()
    
    forensic_handler = ForensicLogHandler()
    # Attach to root and simulation loggers explicitly due to propagate=False
    logging.getLogger().addHandler(forensic_handler)
    logging.getLogger("simulation").addHandler(forensic_handler)
    logging.getLogger("main").addHandler(forensic_handler)

    # 2. Run Simulation
    if stress_test:
        print(f"Initializing Operation Forensics (STRESS TEST: Asset=50.0 for {ticks} ticks)...")
        config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 50.0 
    else:
        print(f"Initializing Diagnostic Forensics ({ticks} ticks, Normal Assets)...")
    
    sim = create_simulation()

    try:
        for i in range(ticks):
            sim.run_tick()
            if (i+1) % 10 == 0:
                print(f"Tick {i+1}/{ticks} complete...")
    except Exception as e:
        print(f"Simulation crashed at tick {sim.time}: {e}")
        import traceback
        traceback.print_exc()

    # 3. Save Raw Records for Gemini Refinement
    if output_log:
        os.makedirs(os.path.dirname(output_log), exist_ok=True)
        if forensic_handler.all_records:
            fieldnames = forensic_handler.all_records[0].keys()
            with open(output_log, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(forensic_handler.all_records)
            print(f"💾 Raw diagnostic logs saved to {output_log}")

    # 4. Analyze Results (Autopsy)
    print(f"\nSimulation Complete. Analyzing {len(forensic_handler.death_records)} deaths...")

    type_a_count = 0
    type_b_count = 0
    type_c_count = 0
    type_d_count = 0
    report_lines = []
    unique_deaths = []
    seen_deaths = set()

    for record in forensic_handler.death_records:
        death_key = (record["tick"], record["agent_id"])
        if death_key not in seen_deaths:
            seen_deaths.add(death_key)
            unique_deaths.append(record)

    sample_cases = []
    for record in unique_deaths:
        death_tick = record["tick"]
        vacancies = record["job_vacancies_available"]
        last_offer = record["last_labor_offer_tick"]
        cash = record["cash_at_death"]
        price = record["market_food_price"]

        # Classification Logic
        is_type_a = vacancies == 0
        is_type_b = (death_tick - last_offer) > 10
        price_val = price if price is not None else 999999.0
        is_type_c = (cash >= price_val)
        is_type_d = (cash < price_val)

        assigned_type = "Type D (Poverty)"
        if is_type_a: assigned_type = "Type A (No Jobs)"; type_a_count += 1
        elif is_type_b: assigned_type = "Type B (Won't Work)"; type_b_count += 1
        elif is_type_c: assigned_type = "Type C (Won't Eat)"; type_c_count += 1
        else: type_d_count += 1

        if len(sample_cases) < 15: 
            sample_cases.append(f"- **{assigned_type}** | Agent #{record['agent_id']} | Tick: {death_tick} | Cash: {cash:.2f} | Vacancies: {vacancies} | Last Offer: {last_offer} | Price: {price}")

    total = len(unique_deaths)
    if total > 0:
        report_lines.append("## Classification Summary")
        report_lines.append(f"- **Type A (No Jobs)**: {type_a_count} ({type_a_count/total:.1%})")
        report_lines.append(f"- **Type B (Won't Work)**: {type_b_count} ({type_b_count/total:.1%})")
        report_lines.append(f"- **Type C (Won't Eat)**: {type_c_count} ({type_c_count/total:.1%})")
        report_lines.append(f"- **Type D (Poverty)**: {type_d_count} ({type_d_count/total:.1%})")
    else:
        report_lines.append("## Classification Summary\n- No deaths recorded.")

    report_lines.append("\n## Sample Cases")
    report_lines.extend(sample_cases)

    os.makedirs("reports", exist_ok=True)
    with open("reports/AUTOPSY_REPORT.md", "w", encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print(f"📄 Forensic report saved to reports/AUTOPSY_REPORT.md")

    # 5. Automated Log Refinement (New)
    save_refined_logs(forensic_handler.all_records, "reports/diagnostic_refined.md")

def save_refined_logs(records: List[Dict[str, Any]], output_path: str):
    """
    Filters high-value forensic events from raw records and saves to Markdown.
    """
    print(f"🔍 [Refinement] Filtering {len(records)} raw records for forensic events...")
    
    keywords = ["SETTLEMENT_FAIL", "starvation", "crash", "STIMULUS_TRIGGERED", "ERROR", "WARNING"]
    refined_lines = ["# Refined Diagnostic Logs", "Critical events extracted for Gemini analysis.\n"]
    
    event_count = 0
    for rec in records:
        msg = str(rec.get("msg", ""))
        level = rec.get("levelname", "INFO")
        
        # Check if any keyword is in the message or if it's an ERROR/WARNING
        if any(kw in msg for kw in keywords) or level in ["ERROR", "WARNING"]:
            tick = rec.get("tick", "?")
            refined_lines.append(f"- **Tick {tick}** | **{level}** | {msg}")
            event_count += 1
            
            # Optionally include forensic fields if available
            forensic_fields = ["agent_id", "cause", "cash_at_death", "market_food_price"]
            details = [f"{k}={rec[k]}" for k in forensic_fields if k in rec]
            if details:
                refined_lines.append(f"  - Details: {', '.join(details)}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(refined_lines))
    
    print(f"✅ Refined logs saved to {output_path} ({event_count} events)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Operation Forensics & Diagnostic Runner")
    parser.add_argument("--ticks", type=int, default=60, help="Number of ticks to run (default: 60)")
    parser.add_argument("--no-stress", action="store_false", dest="stress", help="Run without the 50.0 asset stress test")
    parser.add_argument("--output", type=str, default="logs/diagnostic_raw.csv", help="Path to save raw diagnostic CSV")
    parser.set_defaults(stress=True)
    args = parser.parse_args()
    
    run_forensic_investigation(ticks=args.ticks, stress_test=args.stress, output_log=args.output)
