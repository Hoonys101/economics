import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation

def verify_stability():
    print("--- STABILITY CHECK START (50 Ticks) ---")
    sim = create_simulation()

    try:
        for i in range(50):
            sim.run_tick()
            if i % 10 == 0:
                print(f"Tick {i} complete.")
        print("✅ STABILITY CHECK PASSED")
    except Exception as e:
        print(f"❌ STABILITY CHECK FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_stability()
