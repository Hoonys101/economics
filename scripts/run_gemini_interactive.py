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

def cleanup_key(key):
    """Deletes the executed key from registry using cmd_ops.py"""
    ops_script = BASE_DIR / "scripts" / "cmd_ops.py"
    if ops_script.exists():
        subprocess.run([sys.executable, str(ops_script), "del", key], cwd=BASE_DIR, capture_output=True)
        # We don't print "Deleted" here to keep UI clean, or maybe a small visual cue.
        print(f"🧹 Mission '{key}' removed from registry.")

def main():
    while True: # Loop to refresh registry after deletion
        registry = load_registry()
        
        # Filter only Gemini tasks (those with 'worker' or 'instruction' but no 'command' like 'create')
        gemini_tasks = {}
        for key, data in registry.items():
            if "worker" in data:  # Strict check for worker
                gemini_tasks[key] = data
                
        if not gemini_tasks:
            clear_screen()
            print("==========================================")
            print("   💎 GEMINI MISSION CONTROL")
            print("==========================================")
            print("\n   (No Missions Pending)")
            print("\n   [Ops] To add a mission, Antigravity will use cmd_ops.py")
            print("\n0. Exit")
            input("\nPress Enter to exit...")
            break

        clear_screen()
        print("==========================================")
        print("   💎 GEMINI MISSION CONTROL")
        print("==========================================")
        print(f"Pending Missions: {len(gemini_tasks)}\n")
        
        # Display Menu
        keys = list(gemini_tasks.keys())
        for idx, key in enumerate(keys):
            task = gemini_tasks[key]
            title = key.replace("_", " ").title()
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
                
                # Execute
                result = run_gemini([selected_key], registry)
                
                # Auto-Cleanup: Always remove from list if executed, assuming success or at least consumption
                # If run_gemini returns False/Error, maybe we should ask? 
                # For now, let's assume consumption = delete to keep workflow flowing.
                cleanup_key(selected_key)
                
                input("\n✅ Task Completed & Removed. Press Enter to continue...")
            else:
                print("❌ Invalid selection.")
                input("Press Enter...")
        else:
            print("❌ Invalid input.")
            input("Press Enter...")

if __name__ == "__main__":
    main()
