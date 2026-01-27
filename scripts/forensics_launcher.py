import sys
import os
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import config
import main
import logging

def run_forensics():
    # 1. Configuration Override for 1 Tick
    config.SIMULATION_TICKS = 1
    
    # 2. Force Debug Logging to a specific file
    log_file = root / "logs" / "forensics_tick1.log"
    os.makedirs(log_file.parent, exist_ok=True)
    
    # We clear the file if it exists
    with open(log_file, "w") as f:
        f.write("")

    # Standard logging setup (will use basicConfig fallback if no config file)
    main.setup_logging()
    
    # Set up a FileHandler to catch everything in forensics_tick1.log
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    file_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    print(f"🚀 Running simulation for 1 tick... (Logs: {log_file})")
    
    try:
        main.run_simulation()
        print("✅ Simulation complete.")
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_forensics()
