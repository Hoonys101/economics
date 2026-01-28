
import sys
import os
sys.path.append(os.getcwd())
import logging
from main import create_simulation

# Disable most logging to see clean output
logging.disable(logging.CRITICAL)

def hunt_leak():
    sim = create_simulation()
    state = sim.world_state
    
    def get_snapshot():
        snapshot = {}
        for h in state.households:
            snapshot[f"H_{h.id}"] = h.assets
        for f in state.firms:
            snapshot[f"F_{f.id}"] = f.assets
        if state.bank:
            snapshot["BANK"] = state.bank.assets
        if state.government:
            snapshot["GOVT"] = state.government.assets
        return snapshot

    print("--- LEAK HUNT START ---")
    snap0 = get_snapshot()
    money0 = state.calculate_total_money()
    
    sim.run_tick()
    
    snap1 = get_snapshot()
    money1 = state.calculate_total_money()
    
    delta = money1 - money0
    auth_delta = state.government.get_monetary_delta() if state.government else 0.0
    leak = delta - auth_delta
    
    print(f"Total Money T0: {money0:,.2f}")
    print(f"Total Money T1: {money1:,.2f}")
    print(f"Delta: {delta:,.2f}")
    print(f"Authorized: {auth_delta:,.2f}")
    print(f"Leak: {leak:,.2f}")
    
    print("\n--- Asset Changes ---")
    all_keys = set(snap0.keys()) | set(snap1.keys())
    for k in sorted(all_keys):
        v0 = snap0.get(k, 0.0)
        v1 = snap1.get(k, 0.0)
        diff = v1 - v0
        if abs(diff) > 1e-5:
            print(f"{k}: {v0:,.2f} -> {v1:,.2f} (Diff: {diff:,.2f})")

    # Check for new agents
    new_agents = [k for k in snap1.keys() if k not in snap0]
    if new_agents:
        print(f"\nNew Agents detected: {new_agents}")

if __name__ == "__main__":
    hunt_leak()
