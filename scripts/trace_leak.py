
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from main import create_simulation

def trace():
    print("--- TRACE START ---")
    sim = create_simulation()
    
    print(f"Tick 0 (START) Total Money: {sim.world_state.calculate_total_money():,.2f}")
    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.assets:,.2f}, Active={f.is_active}")
    
    sim.run_tick()
    
    print(f"\nTick 1 (END) Total Money: {sim.world_state.calculate_total_money():,.2f}")
    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.assets:,.2f}, Active={f.is_active}")
        
    # Check if any firm was removed from the list
    all_agent_ids = [a.id for a in sim.world_state.get_all_agents()]
    print(f"\nAll Active Agent IDs: {all_agent_ids}")

if __name__ == "__main__":
    trace()
