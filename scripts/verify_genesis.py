import os
import sys
import logging

# Add the project root to sys.path
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
import config
from utils.logging_manager import setup_logging
from scripts.operation_forensics import ForensicLogHandler

def run_genesis_verification():
    # 1. Setup Logging
    setup_logging()
    
    forensic_handler = ForensicLogHandler()
    logging.getLogger().addHandler(forensic_handler)
    logging.getLogger("simulation").addHandler(forensic_handler)
    logging.getLogger("main").addHandler(forensic_handler)
    
    # 2. Configure Genesis Parameters
    config.GOVERNMENT_STIMULUS_ENABLED = False
    
    prod_factor = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    cons_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    overrides = {
        "SIMULATION_TICKS": 1000,
        "FIRM_PRODUCTIVITY_FACTOR": prod_factor,
        "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK": cons_rate,
        "GOVERNMENT_STIMULUS_ENABLED": False,
        "INITIAL_HOUSEHOLD_ASSETS_MEAN": config.INITIAL_HOUSEHOLD_ASSETS_MEAN,
        "INITIAL_FIRM_CAPITAL_MEAN": config.INITIAL_FIRM_CAPITAL_MEAN
    }
    
    print(f"--- 🚀 Operation Genesis Verification ---")
    print(f"Ticks: {overrides['SIMULATION_TICKS']}")
    print(f"Productivity: {prod_factor}")
    print(f"Consumption: {cons_rate}")
    print(f"Stimulus: {overrides['GOVERNMENT_STIMULUS_ENABLED']}")
    print(f"------------------------------------------")

    # 3. Create and Run Simulation
    sim = create_simulation(overrides=overrides)
    
    simulation_ticks = overrides.get("SIMULATION_TICKS", 100)
    for i in range(simulation_ticks):
        sim.run_tick()
        if (i + 1) % 100 == 0:
            print(f"Tick {i+1}/{simulation_ticks} complete...")

    # 4. Analyze Results
    unique_deaths = set()
    unique_stimulus = []
    
    type_a_count = 0 
    type_b_count = 0 
    type_c_count = 0 
    type_d_count = 0 
    
    report_lines = []
    sample_cases = []

    for record_dict in forensic_handler.all_records:
        msg = record_dict.get("msg", "")
        
        if "AGENT_DEATH" in msg or "starvation" in record_dict.get("cause", ""):
            death_tick = record_dict.get("tick", 0)
            agent_id = record_dict.get("agent_id")
            
            if (death_tick, agent_id) in unique_deaths:
                continue
            unique_deaths.add((death_tick, agent_id))
            
            cash = record_dict.get("cash_at_death", 0.0)
            vacancies = record_dict.get("job_vacancies_available", 0)
            price = record_dict.get("market_food_price", 0.0)
            
            if vacancies == 0:
                type_a_count += 1
                assigned_type = "Type A (No Jobs)"
            elif not price or price <= 0:
                type_b_count += 1
                assigned_type = "Type B (No Food)"
            elif cash < (price or 1.0):
                type_d_count += 1
                assigned_type = "Type D (Poverty)"
            else:
                assigned_type = "Unclassified"

            if len(sample_cases) < 15: 
                sample_cases.append(f"- **{assigned_type}** | Agent #{agent_id} | Tick: {death_tick} | Cash: {cash:.2f} | Vacancies: {vacancies} | Price: {price}")
        
        elif "STIMULUS_TRIGGERED" in msg:
            unique_stimulus.append(record_dict)

    # Generate Report
    total_deaths = len(unique_deaths)
    
    report_lines.append("# 🚀 Operation Genesis: Verification Report")
    report_lines.append(f"- **Total Ticks**: {overrides['SIMULATION_TICKS']}")
    report_lines.append(f"- **Total Deaths**: {total_deaths}")
    report_lines.append(f"- **Type A (No Jobs)**: {type_a_count}")
    report_lines.append(f"- **Type B (No Food)**: {type_b_count}")
    report_lines.append(f"- **Type D (Poverty)**: {type_d_count}")
    report_lines.append(f"- **Gov Stimulus Count**: {len(unique_stimulus)}")
    report_lines.append("")
    report_lines.append("## Survival Rate")
    survival_rate = (1.0 - (total_deaths / config.NUM_HOUSEHOLDS)) if config.NUM_HOUSEHOLDS > 0 else 0
    report_lines.append(f"**Survival Rate: {survival_rate:.1%}**")
    report_lines.append("")
    report_lines.append("## Sample Cases")
    for case in sample_cases:
        report_lines.append(case)

    print("\n".join(report_lines))

    os.makedirs("reports", exist_ok=True)
    with open("reports/GENESIS_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"\nReport saved to reports/GENESIS_REPORT.md")

if __name__ == "__main__":
    run_genesis_verification()
