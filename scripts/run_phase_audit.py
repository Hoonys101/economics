
import sys
import os
import logging
import json

# Ensure the root directory is in sys.path
sys.path.append(os.getcwd())

from modules.system.builders.simulation_builder import create_simulation
from simulation.orchestration.phases import (
    Phase0_PreSequence, Phase_Production, Phase1_Decision, Phase2_Matching,
    Phase3_Transaction, Phase_Bankruptcy, Phase_HousingSaga, Phase_Consumption, Phase5_PostSequence,
    Phase_BankAndDebt, Phase_FirmProductionAndSalaries, Phase_GovernmentPrograms, Phase_TaxationIntents,
    Phase_MonetaryProcessing
)
from modules.system.api import DEFAULT_CURRENCY

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_total_assets(sim):
    """
    Calculate Total Assets (Sum of Balances for HH + Firm + Gov + Bank).
    Using get_balance(DEFAULT_CURRENCY).
    This effectively tracks M0 (Base Money) in circulation among these agents.
    """
    total = 0.0

    # Households
    for hh in sim.households:
        total += hh.get_balance(DEFAULT_CURRENCY)

    # Firms
    for firm in sim.firms:
        total += firm.get_balance(DEFAULT_CURRENCY)

    # Government
    if sim.government:
        total += sim.government.get_balance(DEFAULT_CURRENCY)

    # Bank
    if sim.bank:
        # Bank's get_balance usually returns Reserves (Assets)
        total += sim.bank.get_balance(DEFAULT_CURRENCY)

    return total

def calculate_m2(sim):
    """
    Calculate M2 Money Supply using WorldState.calculate_total_money().
    """
    m2_dict = sim.world_state.calculate_total_money()
    return m2_dict.get(DEFAULT_CURRENCY, 0.0)

def main():
    logger.info("Initializing Simulation...")
    sim = create_simulation()

    # Run Tick 0 to initialize everything properly
    # This advances time to 1 and runs phases for Tick 1 implicitly?
    # No, sim.run_tick() advances time then runs.
    # Init state: time=0.
    # We want to manually execute Tick 1.
    # So we should skip sim.run_tick().

    # However, create_simulation leaves time=0.
    # To run Tick 1 manually:

    # 1. Advance Time
    sim.world_state.time = 1
    logger.info(f"--- Starting Audit for Tick {sim.world_state.time} ---")

    # 2. Tick Setup (Replicating TickOrchestrator.run_tick logic)
    # Reset flow counters
    if sim.world_state.government and hasattr(sim.world_state.government, "reset_tick_flow"):
        sim.world_state.government.reset_tick_flow()

    # Create SimulationState DTO
    # passing None for injectable_sensory_dto as per normal tick start without intervention
    sim_state = sim.tick_orchestrator._create_simulation_state_dto(None)

    # Prepare Audit Log
    results = []

    # Initial State
    initial_assets = calculate_total_assets(sim)
    initial_m2 = calculate_m2(sim)
    results.append({
        "Phase": "Start",
        "Total Assets": initial_assets,
        "Delta Assets": 0.0,
        "M2": initial_m2,
        "Delta M2": 0.0
    })

    prev_assets = initial_assets
    prev_m2 = initial_m2

    # 3. Execute Phases
    phases = sim.tick_orchestrator.phases

    for phase in phases:
        phase_name = phase.__class__.__name__
        logger.info(f"Executing Phase: {phase_name}")

        # Execute
        sim_state = phase.execute(sim_state)

        # Sync
        sim.tick_orchestrator._drain_and_sync_state(sim_state)

        # Audit
        current_assets = calculate_total_assets(sim)
        current_m2 = calculate_m2(sim)

        delta_assets = current_assets - prev_assets
        delta_m2 = current_m2 - prev_m2

        results.append({
            "Phase": phase_name,
            "Total Assets": current_assets,
            "Delta Assets": delta_assets,
            "M2": current_m2,
            "Delta M2": delta_m2
        })

        prev_assets = current_assets
        prev_m2 = current_m2

    # 4. Output Results
    # Create directory
    output_dir = "reports/temp"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "phase_audit.log")

    # Table Header
    header = f"{'Phase':<40} | {'Total Assets':<20} | {'Delta Assets':<15} | {'M2':<20} | {'Delta M2':<15}"
    separator = "-" * len(header)

    output_lines = []
    output_lines.append(header)
    output_lines.append(separator)

    for row in results:
        line = f"{row['Phase']:<40} | {row['Total Assets']:<20.2f} | {row['Delta Assets']:<15.2f} | {row['M2']:<20.2f} | {row['Delta M2']:<15.2f}"
        output_lines.append(line)

    output_text = "\n".join(output_lines)

    print("\n" + output_text + "\n")

    with open(output_file, "w") as f:
        f.write(output_text)

    logger.info(f"Audit saved to {output_file}")

if __name__ == "__main__":
    main()
