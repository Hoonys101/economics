
import sys
import os
sys.path.append(os.getcwd())
import logging
from modules.system.api import DEFAULT_CURRENCY
from main import create_simulation

# Disable most logging to see clean output
logging.disable(logging.CRITICAL)

def hunt_leak():
    sim = create_simulation()
    state = sim.world_state
    
    def get_val(assets):
        if isinstance(assets, dict):
            return assets.get(DEFAULT_CURRENCY, 0.0)
        return assets

    def get_snapshot():
        snapshot = {}
        for h in state.households:
            snapshot[f"H_{h.id}"] = get_val(h._econ_state.assets)
        for f in state.firms:
            snapshot[f"F_{f.id}"] = get_val(f.assets)
        if state.bank:
            snapshot["BANK"] = get_val(state.bank.assets)
        if state.central_bank:
            snapshot["CB"] = get_val(state.central_bank.assets)
        if state.governments:
            snapshot["GOVT"] = get_val(state.governments[0].assets)
        return snapshot

    print("--- LEAK HUNT START ---")
    snap0 = get_snapshot()
    money0 = state.get_total_system_money_for_diagnostics()
    
    sim.run_tick()
    
    snap1 = get_snapshot()
    money1 = state.get_total_system_money_for_diagnostics()
    
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
