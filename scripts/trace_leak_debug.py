
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

print("DEBUG | Importing create_simulation...")
from main import create_simulation
print("DEBUG | Import complete.")

def trace():
    print("--- TRACE START ---")
    print("DEBUG | Initializing simulation...")
    sim = create_simulation()
    print("DEBUG | Simulation initialized.")
    
    print(f"Tick 0 (START) Total Money: {sim.world_state.get_total_system_money_for_diagnostics():,.2f}")
    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.assets:,.2f}, Active={f.is_active}")
    
    print("DEBUG | Running Tick 1...")
    sim.run_tick()
    print("DEBUG | Tick 1 complete.")
    
    print(f"\nTick 1 (END) Total Money: {sim.world_state.get_total_system_money_for_diagnostics():,.2f}")
    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.assets:,.2f}, Active={f.is_active}")
        
    # Check if any firm was removed from the list
    all_agent_ids = [a.id for a in sim.world_state.get_all_agents()]
    print(f"\nAll Active Agent IDs: {all_agent_ids}")

if __name__ == "__main__":
    trace()
