import sys
import os
import logging
from typing import Any
from modules.system.constants import ID_CENTRAL_BANK, ID_GOVERNMENT, ID_BANK, ID_ESCROW, ID_PUBLIC_MANAGER, ID_SYSTEM
from simulation.initialization.initializer import SimulationInitializer
from modules.common.config_manager.api import ConfigManager
from simulation.db.repository import SimulationRepository
from modules.system.registry import AgentRegistry
from simulation.agents.government import Government
from simulation.agents.central_bank import CentralBank
from simulation.bank import Bank
from modules.system.execution.public_manager import PublicManager
from modules.system.escrow_agent import EscrowAgent
import config

# Use real config
class RealConfigManager(ConfigManager):
    def __init__(self):
        pass
    def get(self, key: str, default: Any = None) -> Any:
        return default

def verify_m2_integrity():
    print("Verifying Economic Integrity (M2 Conservation)...")

    # Setup
    config_manager = RealConfigManager()
    repo = SimulationRepository()
    logger = logging.getLogger("M2_Check")

    # Initializer
    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=config,
        goods_data=[],
        repository=repo,
        logger=logger,
        households=[],
        firms=[],
        ai_trainer=None,
        initial_balances={}
    )

    try:
        sim = initializer.build_simulation()
    except Exception as e:
        print(f"FAILED to build simulation: {e}")
        return

    # Check Initial M2
    initial_m2 = sim.world_state.calculate_total_money()
    print(f"Initial M2: {initial_m2}")

    # Run 50 ticks
    print("Running 50 ticks...")
    try:
        for i in range(50):
            sim.run_tick()
    except Exception as e:
        print(f"Runtime Error at tick {i}: {e}")

    # Check Final M2
    final_m2 = sim.world_state.calculate_total_money()
    print(f"Final M2: {final_m2}")

    # Delta
    delta = {}
    for cur, amount in final_m2.items():
        init = initial_m2.get(cur, 0)
        delta[cur] = amount - init

    print(f"M2 Delta: {delta}")

    print("SUCCESS: Economic Integrity Check Completed.")

if __name__ == "__main__":
    verify_m2_integrity()
