
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from main import create_simulation
from modules.system.api import DEFAULT_CURRENCY

def test_tick_crash():
    print("🚀 [Diagnostic] Starting 2-tick test...")
    sim = create_simulation()
    
    try:
        print("Tick 1...")
        sim.run_tick()
        print("✅ Tick 1 Success.")
        
        print("Tick 2...")
        sim.run_tick()
        print("✅ Tick 2 Success.")
        
    except Exception as e:
        print(f"❌ CRASH DETECTED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tick_crash()
