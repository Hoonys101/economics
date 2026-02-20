
import sys
import logging
from pathlib import Path
from collections import defaultdict

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from modules.system.builders.simulation_builder import create_simulation
from modules.system.api import DEFAULT_CURRENCY
from simulation.orchestration.phases import *
from simulation.orchestration.phases.intercept import Phase0_Intercept
from simulation.orchestration.phases.system_commands import Phase_SystemCommands
from simulation.orchestration.phases_recovery import Phase_SystemicLiquidation
from simulation.orchestration.phases.scenario_analysis import Phase_ScenarioAnalysis

def audit_money(sim, context_name):
    # Core Money Audit Logic
    h_sum = sum(h.total_wealth for h in sim.world_state.households)
    f_sum = sum(f.total_wealth for f in sim.world_state.firms)
    gov_sum = sim.world_state.government.total_wealth if sim.world_state.government else 0
    bank_wealth = sim.world_state.bank.total_wealth if sim.world_state.bank else 0
    
    total = h_sum + f_sum + gov_sum + bank_wealth
    
    # Check for money sitting in pending transactions (if any)
    # The current engine handles transactions in a specific phase, but let's check
    pending_tx_vol = 0
    if hasattr(sim.world_state, 'transactions'):
        # This shows processed transactions, not pending ones usually, 
        # but depends on the phase.
        pass

    return {
        "context": context_name,
        "total": total,
        "h": h_sum,
        "f": f_sum,
        "gov": gov_sum,
        "bank": bank_wealth
    }

def run_master_audit():
    # Setup
    sim = create_simulation()
    reports = []
    
    # 1. INITIAL STATE
    reports.append(audit_money(sim, "INITIAL_EMPTY"))
    
    # 2. AFTER INITIALIZATION (Normally handled inside create_simulation/Bootstrapper)
    # Since create_simulation runs bootstrapper, this is the "Ready" state.
    reports.append(audit_money(sim, "POST_BOOTSTRAP"))
    
    # Manually Orchestrate Tick 1 Phases
    state = sim.world_state
    sim_state = sim._create_simulation_state_dto()
    
    # Replicate TickOrchestrator phases
    phases = [
        ("Phase0_Intercept", Phase0_Intercept(state)),
        ("Phase0_PreSequence", Phase0_PreSequence(state)),
        ("Phase_SystemCommands", Phase_SystemCommands(state)),
        ("Phase_Production", Phase_Production(state)),
        ("Phase1_Decision", Phase1_Decision(state)),
        ("Phase_Bankruptcy", Phase_Bankruptcy(state)),
        ("Phase_HousingSaga", Phase_HousingSaga(state)),
        ("Phase_SystemicLiquidation", Phase_SystemicLiquidation(state)),
        ("Phase2_Matching", Phase2_Matching(state)),
        ("Phase_BankAndDebt", Phase_BankAndDebt(state)),
        ("Phase_FirmProductionAndSalaries", Phase_FirmProductionAndSalaries(state)),
        ("Phase_GovernmentPrograms", Phase_GovernmentPrograms(state)),
        ("Phase_TaxationIntents", Phase_TaxationIntents(state)),
        ("Phase_MonetaryProcessing", Phase_MonetaryProcessing(state)),
        ("Phase3_Transaction", Phase3_Transaction(state)),
        ("Phase_Consumption", Phase_Consumption(state)),
        ("Phase5_PostSequence", Phase5_PostSequence(state))
    ]
    
    last_total = reports[-1]["total"]
    
    print(f"{'Phase Name':<35} | {'Total M2':>15} | {'Delta':>12}")
    print("-" * 68)
    print(f"{reports[-1]['context']:<35} | {reports[-1]['total']:15,} | {'0':>12}")

    for name, phase in phases:
        sim_state = phase.execute(sim_state)
        sim._drain_and_sync_state(sim_state)
        
        current_audit = audit_money(sim, name)
        delta = current_audit["total"] - last_total
        
        marker = " [!!!]" if abs(delta) > 0 else ""
        print(f"{name:<35} | {current_audit['total']:15,} | {delta:12,}{marker}")
        
        last_total = current_audit["total"]
        reports.append(current_audit)

if __name__ == "__main__":
    run_master_audit()
