import time
import logging
import numpy as np
import random
from dataclasses import dataclass
from typing import Dict, Any, List

# Mock Classes and DTOs
@dataclass
class MockConfig:
    TECH_FERTILIZER_MULTIPLIER: float = 3.0
    TECH_UNLOCK_COST_THRESHOLD: float = 5000.0
    TECH_DIFFUSION_RATE: float = 0.05
    TECH_UNLOCK_PROB_CAP: float = 0.1

class MockLogger:
    def info(self, msg, extra=None):
        pass
    def warning(self, msg, extra=None):
        pass

# Import TechnologyManager (assuming it's in the python path)
import sys
import os
sys.path.append(os.getcwd())

from simulation.systems.technology_manager import TechnologyManager
from simulation.systems.tech.api import FirmTechInfoDTO

def run_benchmark():
    print("--- Starting TechnologyManager Benchmark ---")

    # Setup
    config = MockConfig()
    logger = MockLogger()
    tech_manager = TechnologyManager(config, logger)

    # Create 2500 mock firms
    num_firms = 2500
    firms: List[FirmTechInfoDTO] = []

    sectors = ["FOOD", "MANUFACTURING", "SERVICES"]

    for i in range(num_firms):
        firms.append({
            "id": i + 1, # ID starts from 1
            "sector": random.choice(sectors),
            "current_rd_investment": random.uniform(0, 1000)
        })

    # Unlock the tech manually to enable diffusion testing
    # The default tech is "TECH_AGRI_CHEM_01"
    if "TECH_AGRI_CHEM_01" in tech_manager.tech_tree:
        tech_manager._unlock_tech(tech_manager.tech_tree["TECH_AGRI_CHEM_01"], 0)
    else:
        print("Error: Default tech not found!")
        return

    human_capital_index = 1.5

    # Run Loop
    num_ticks = 100
    start_time = time.time()

    initial_adoptions = sum([1 for f in firms if tech_manager.has_adopted(f["id"], "TECH_AGRI_CHEM_01")])

    for tick in range(num_ticks):
        tech_manager.update(tick, firms, human_capital_index)

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / num_ticks

    final_adoptions = sum([1 for f in firms if tech_manager.has_adopted(f["id"], "TECH_AGRI_CHEM_01")])

    print(f"Total Time: {total_time:.4f}s")
    print(f"Average Time per Tick: {avg_time*1000:.4f}ms")
    print(f"Initial Adoptions: {initial_adoptions}")
    print(f"Final Adoptions: {final_adoptions}")

    # Functional Assertion
    if final_adoptions <= initial_adoptions:
        print("FAILURE: No diffusion occurred!")
        sys.exit(1)

    # Performance Assertion
    target_ms = 10.0
    if avg_time * 1000 > target_ms:
        print(f"FAILURE: Performance target missed! ({avg_time*1000:.4f}ms > {target_ms}ms)")
        sys.exit(1)
    else:
        print("SUCCESS: Performance target met!")

if __name__ == "__main__":
    run_benchmark()
