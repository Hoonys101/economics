import traceback
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from scripts.stress_test_validation import run_validation

try:
    print("Starting debug run...")
    run_validation(100, 'phase29_depression')
    print("Debug run completed successfully (unexpectedly).")
except Exception as e:
    print("\n" + "!"*50)
    print("CRASH DETECTED")
    print("!"*50)
    traceback.print_exc()
    print("!"*50)
