import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.getcwd())

from main import create_simulation

def smoke_test():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SmokeTest")

    logger.info("Initializing Simulation...")
    try:
        sim = create_simulation()
    except Exception as e:
        logger.error(f"Initialization Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("Running 10 Ticks...")
    try:
        for i in range(10):
            logger.info(f"--- Tick {i+1} ---")
            sim.run_tick()
    except Exception as e:
        logger.error(f"Simulation Crashed at Tick {sim.time}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("Smoke Test Passed!")

if __name__ == "__main__":
    smoke_test()
