import sys
from pathlib import Path
import os
import logging

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.db.repository import SimulationRepository
import config
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.ai.api import Personality

def diagnose():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("DeadlockDiagnosis")

    # 1. Initialize Simulation (Headless)
    # Use a dummy repo or real one? Real one is fine, it creates a new run_id.
    # repo = SimulationRepository()

    # Create Agents
    talent = Talent(base_learning_rate=0.1, max_potential={})
    households = [
        Household(id=i, talent=talent, goods_data=[], initial_assets=1000, initial_needs={'survival': 0}, decision_engine=AIDrivenHouseholdDecisionEngine(None, config), value_orientation="test", personality=Personality.MISER, config_module=config)
        for i in range(10)
    ]
    # Create Firms (Mixed Specialization)
    firms = []
    for i in range(5):
        spec = list(config.GOODS.keys())[i % len(config.GOODS)]
        f = Firm(
            id=100+i,
            initial_capital=1000.0,
            initial_liquidity_need=100.0,
            specialization=spec,
            productivity_factor=1.0,
            decision_engine=AIDrivenFirmDecisionEngine(None, config),
            value_orientation="Profit",
            config_module=config
        )
        firms.append(f)

    # Note: We don't need full engine run, just init state.
    # But Engine init calls Bootstrapper (Target State).
    # To Diagnose the "Before" state, we check firms BEFORE engine init or disable bootstrapper?
    # Actually, this script is to *confirm* the deadlock on a RAW firm.

    print("--- DIAGNOSIS REPORT: PRE-BOOTSTRAPPER ---")
    for firm in firms:
        inputs_needed = config.GOODS.get(firm.specialization, {}).get("inputs", {})

        print(f"[Firm {firm.id} | {firm.specialization}]")
        print(f"  Assets: {firm.assets}")
        print(f"  Inputs Required: {inputs_needed}")
        print(f"  Input Inventory: {firm.input_inventory}")

        # Deadlock Check
        if inputs_needed and not firm.input_inventory:
            print("  -> STATUS: DEADLOCK (No Inputs)")
        elif firm.assets < 500: # Arbitrary low cash
            print("  -> STATUS: RISK (Low Cash)")
        else:
            print("  -> STATUS: OK")

if __name__ == "__main__":
    diagnose()
