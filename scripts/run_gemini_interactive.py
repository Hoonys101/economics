import sys
import json
import os
from pathlib import Path
import subprocess

# Add scripts dir to path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR / "scripts"))

try:
    from launcher import run_gemini, load_registry
except ImportError:
    print("❌ Critical: Could not import launcher module.")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    registry = load_registry()
    
    # Filter only Gemini tasks (those with 'worker' or 'instruction' but no 'command' like 'create')
    gemini_tasks = {}
    for key, data in registry.items():
        if "worker" in data and "instruction" in data:
            gemini_tasks[key] = data
            
    if not gemini_tasks:
        print("⚠️ No Gemini tasks found in command_registry.json")
        return

    while True:
        clear_screen()
        print("==========================================")
        print("   💎 GEMINI MISSION CONTROL")
        print("==========================================")
        print(f"Loaded {len(gemini_tasks)} missions from registry.\n")
        
        # Display Menu
        keys = list(gemini_tasks.keys())
        for idx, key in enumerate(keys):
            task = gemini_tasks[key]
            # Try to get a clean title or use key
            title = key.replace("_", " ").title()
            # If instruction is long, truncate
            inst_preview = task.get("instruction", "")[:60].replace("\n", " ")
            print(f"{idx + 1}. {title}")
            print(f"   └─ [{task.get('worker', 'unknown')}] {inst_preview}...")
        
        print("\n0. Exit")
        
        choice = input("\nSelect Mission (0-{}): ".format(len(keys))).strip()
        
        if choice == '0':
            print("Bye.")
            break
            
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                selected_key = keys[idx]
                print(f"\n🚀 Launching: {selected_key}")
                
                # Use the existing logic in launcher.py
                # We simulate argv passing: [key]
                run_gemini([selected_key], registry)
                
                input("\n✅ Task Completed. Press Enter to continue...")
            else:
                print("❌ Invalid selection.")
                input("Press Enter...")
        else:
            print("❌ Invalid input.")
            input("Press Enter...")

if __name__ == "__main__":
    main()
