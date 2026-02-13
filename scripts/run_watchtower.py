import sys
import os
import logging
import time
import queue

# Add project root to sys.path
sys.path.append(os.getcwd())

from utils.logging_manager import setup_logging
from utils.simulation_builder import create_simulation
from modules.system.server_bridge import CommandQueue, TelemetryExchange
from modules.system.server import SimulationServer
import config

def main():
    # 1. Setup Logging
    setup_logging()
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger("WatchtowerLauncher")

    # 2. Initialize Bridge
    cmd_queue = CommandQueue()
    telemetry_exchange = TelemetryExchange()

    # 3. Start Server
    HOST = "0.0.0.0"
    PORT = 8765
    server = SimulationServer(HOST, PORT, cmd_queue, telemetry_exchange)
    server.start()

    # 4. Initialize Simulation
    logger.info("Initializing Simulation Engine...")
    sim = create_simulation()

    # 5. Inject Bridge into WorldState
    sim.world_state.command_queue = cmd_queue
    sim.world_state.telemetry_exchange = telemetry_exchange

    # 6. Run Engine Loop
    logger.info("Starting Engine Loop...")
    try:
        while True:
            start_time = time.time()
            sim.run_tick()
            duration = time.time() - start_time

            # Cap at 10 TPS roughly for visual sanity
            if duration < 0.1:
                time.sleep(0.1 - duration)

    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    except Exception as e:
        logger.critical(f"Simulation crashed: {e}", exc_info=True)
    finally:
        sim.finalize_simulation()

if __name__ == "__main__":
    main()
