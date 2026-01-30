
import sys
import os
sys.path.append(os.getcwd())
from main import create_simulation
from simulation.tick_scheduler import TickScheduler

def debug_tick():
    print("--- DEBUG TICK PHASES START ---")
    sim = create_simulation()
    
    # Baseline
    money_0 = sim.world_state.calculate_total_money()
    print(f"Money Start: {money_0:,.2f}")
    
    scheduler = TickScheduler(sim.world_state, sim.action_processor)
    state = sim.world_state
    
    # 1. Pre-Sequence (Tick start, events, etc)
    scheduler._phase_pre_sequence_stabilization(state)
    state.time += 1
    
    if state.event_system:
         # Simplified call for debug
         context = {
             "households": state.households,
             "firms": state.firms,
             "markets": state.markets,
             "government": state.government,
             "central_bank": state.central_bank,
             "bank": state.bank
         }
         state.event_system.execute_scheduled_events(state.time, context, state.stress_scenario_config)

    money_1 = sim.world_state.calculate_total_money()
    print(f"Post-Event Money: {money_1:,.2f} (Delta: {money_1 - money_0:,.2f})")
    
    # 2. Decisions & Transaction Generation
    # Be careful, TickScheduler.run_tick does a lot of logic inline.
    # We can't easily decompose it without replicating logic.
    # Instead, let's inject a "Money Check" into TickScheduler itself?
    # Or just run the full tick and use logging.
    
    # Let's run the full tick but print logs are tricky.
    # Better: Inspect the transactions generated.
    
    scheduler.run_tick()
    
    money_end = sim.world_state.calculate_total_money()
    delta = money_end - money_0
    
    authorized = 0.0
    if hasattr(sim.government, "get_monetary_delta"):
        authorized = sim.government.get_monetary_delta()
        
    print(f"Money End: {money_end:,.2f}")
    print(f"Total Delta: {delta:,.2f}")
    print(f"Authorized: {authorized:,.2f}")
    print(f"Leak: {delta - authorized:,.2f}")

if __name__ == "__main__":
    debug_tick()
