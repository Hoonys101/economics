
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from modules.system.api import IAgentRegistry
    print("SUCCESS: IAgentRegistry imported successfully.")
except ImportError as e:
    print(f"FAILURE: {e}")
except Exception as e:
    print(f"ERROR: {e}")
