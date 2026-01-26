
import sys
import os
sys.path.append(os.getcwd())
from main import create_simulation

def probe():
    print("--- PROBE START ---")
    sim = create_simulation()
    
    if not sim.households:
        print("No households found!")
        return

    h = sim.households[0]
    print(f"Household {h.id} Needs: {h.needs}")
    
    if "survival" in h.needs:
        print("SUCCESS: 'survival' key found.")
    else:
        print("FAILURE: 'survival' key MISSING.")

if __name__ == "__main__":
    probe()
