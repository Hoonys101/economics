import sys
import os
import logging
from modules.system.builders.simulation_builder import create_simulation
import config

# Setup logging to file
os.makedirs("reports/diagnostics", exist_ok=True)
log_file = "reports/diagnostics/runtime_audit.log"

# Configure root logger to output to file
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.DEBUG)

def run_diagnostic(ticks=80):
    print(f"Starting diagnostic run for {ticks} ticks...")
    
    # Overrides for short run
    overrides = {
        "SIMULATION_TICKS": ticks,
        "RANDOM_SEED": 42
    }
    
    try:
        sim = create_simulation(overrides=overrides)
        
        for i in range(ticks):
            if i % 10 == 0:
                print(f"Tick {i}...")
            sim.run_tick()
            
        print("Diagnostic run completed successfully.")
    except Exception as e:
        print(f"Diagnostic run crashed: {e}")
        root_logger.error(f"FATAL_CRASH: {e}", exc_info=True)
    finally:
        if 'sim' in locals():
            sim.repository.close()

if __name__ == "__main__":
    run_diagnostic(80)
