import sys
import json
import os
from pathlib import Path
import subprocess

# Add scripts dir to path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR / "scripts"))

try:
    from jules_bridge import JulesBridge, get_my_sessions, register_session, AutomationMode, check_jules_status
    from launcher import load_registry
except ImportError:
    print("❌ Critical: Could not import jules_bridge module.")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_file_content(filepath_str):
    """Safely read file content with encoding handling."""
    path = BASE_DIR / filepath_str
    if not path.exists():
        print(f"❌ File not found: {path}")
        return None
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def run_create_menu(registry, bridge):
    clear_screen()
    print("==========================================")
    print("   ⚡ JULES: NEW MISSION")
    print("==========================================")
    
    # Filter Jules creation tasks from registry
    jules_tasks = {}
    for key, data in registry.items():
        if data.get("command") == "create":
            jules_tasks[key] = data
            
    if not jules_tasks:
        print("⚠️ No Jules 'create' missions found in command_registry.json")
        input("Press Enter to return...")
        return

    keys = list(jules_tasks.keys())
    for idx, key in enumerate(keys):
        task = jules_tasks[key]
        print(f"{idx + 1}. {task.get('title', key)}")
        print(f"   └─ {task.get('instruction', '')[:60]}...")
        
    print("\nC. Custom Manual Mission")
    print("0. Back")
    
    choice = input("\nSelect Mission: ").strip().upper()
    
    if choice == '0': return
    
    title = ""
    instruction = ""
    
    if choice == 'C':
        title = input("Enter Task Title: ")
        print("Select Instruction Source:")
        print("1. Type Now")
        print("2. Load from File")
        
        src = input("Select (1-2): ").strip()
        if src == '1':
            instruction = input("Enter Instruction: ")
        elif src == '2':
            fpath = input("Enter File Path (rel to project): ")
            content = get_file_content(fpath)
            if not content:
                input("Aborted. Press Enter...")
                return
            instruction = content
        else:
            return

        # Auto-sync Git
        print("\n🔄 Syncing Git before dispatch...")
        bridge.sync_git(title)
        
        print(f"\n🚀 Dispatching Custom Jules: {title}")
        try:
            session = bridge.create_session(
                prompt=instruction,
                title=title,
                automation_mode=AutomationMode.AUTO_CREATE_PR
            )
            register_session(session.id, title, instruction[:100] + "...")
            print(f"\n✅ Session Created! ID: {session.id}")
            input("Press Enter...")
        except Exception as e:
            print(f"❌ Failed: {e}")
            input("Press Enter...")
        return

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            key = keys[idx]
            task = jules_tasks[key]
            title = task.get('title', key)
            instruction = task.get('instruction', "")
            
            # File injection for create
            if task.get("file"):
                f_content = get_file_content(task["file"])
                if f_content:
                    instruction += f"\n\n[File Content: {task['file']}]\n```\n{f_content}\n```"

            print("\n🔄 Syncing Git before dispatch...")
            bridge.sync_git(title)
            
            print(f"\n🚀 Dispatching {key}: {title}")
            try:
                session = bridge.create_session(
                    prompt=instruction,
                    title=title,
                    automation_mode=AutomationMode.AUTO_CREATE_PR
                )
                register_session(session.id, title, instruction[:100] + "...")
                print(f"\n✅ Session Created! ID: {session.id}")
                input("Press Enter...")
            except Exception as e:
                print(f"❌ Failed: {e}")
                input("Press Enter...")
        else:
            print("❌ Invalid selection")

def run_reply_menu(bridge, registry):
    clear_screen()
    print("==========================================")
    print("   💬 JULES: COMMUNICATE")
    print("==========================================")
    
    sessions = get_my_sessions()
    if not sessions:
        print("⚠️ No active sessions found.")
        input("Press Enter...")
        return
        
    valid_sessions = []
    idx = 1
    for sid, data in sessions.items():
        title = data if isinstance(data, str) else data.get("title", "Unknown")
        print(f"{idx}. {title} ({sid})")
        valid_sessions.append(sid)
        idx += 1
        
    print("\n0. Back")
    
    sel = input("\nSelect Session: ").strip()
    if sel == '0': return
    
    if sel.isdigit() and 1 <= int(sel) <= len(valid_sessions):
        sid = valid_sessions[int(sel)-1]
        
        # Show recent history
        print("\nfetching recent activity...")
        try:
            acts = bridge.list_activities(sid, page_size=2)
            for act in reversed(acts):
                 desc = act.get("description", "")[:100]
                 print(f"   [{act.get('type')}] {desc}...")
        except Exception as e:
            print(f"⚠️ Failed to fetch history: {e}")

        # --- REVISED: Pre-loaded Only ---
        reply_tasks = {k: v for k, v in registry.items() if v.get("command") == "send-message"}
        
        if not reply_tasks:
            print("\n⚠️ No 'send-message' tasks found in registry.")
            print("   Please add one to command_registry.json first.")
            input("Press Enter...")
            return

        print("\n--- Select Reply Template ---")
        r_keys = list(reply_tasks.keys())
        for i, rk in enumerate(r_keys):
            task = reply_tasks[rk]
            # Preview instruction
            preview = task.get("instruction", "")[:40].replace("\n", " ")
            file_hint = f" (File: {task.get('file')})" if task.get("file") else ""
            print(f"{i+1}. {rk}{file_hint} -> \"{preview}...\"")
            
        r_sel = input("\nSelect Reply (1-{}): ".format(len(r_keys))).strip()
        
        if r_sel.isdigit():
            r_idx = int(r_sel) - 1
            if 0 <= r_idx < len(r_keys):
                key = r_keys[r_idx]
                task = reply_tasks[key]
                message = task.get("instruction", "")
                
                # File Injection Logic
                if task.get("file"):
                    f_content = get_file_content(task["file"])
                    if f_content:
                         message += f"\n\n[File Content: {task['file']}]\n```\n{f_content}\n```"
                    else:
                        print(f"⚠️ Warning: Could not read file {task['file']}, sending instruction only.")
                
                print(f"\n🚀 Sending Message ({len(message)} chars)...")
                try:
                    bridge.send_message(sid, message)
                    print("✅ Sent.")
                    
                    if input("Wait for reply? (y/n): ").lower() == 'y':
                        resp = bridge.wait_for_agent_response(sid)
                        if resp:
                            print(f"\n🤖 Jules: {resp.get('description', '')}")
                    input("Press Enter...")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    input("Press Enter...")
            else:
                print("❌ Invalid Selection")
        else:
             print("❌ Invalid Input")

def main():
    bridge = JulesBridge()
    registry = load_registry()
    
    while True:
        clear_screen()
        print("==========================================")
        print("   ⚡ JULES COMMAND CENTER")
        print("==========================================")
        print("1. 🚀 NEW MISSION (Create Session)")
        print("2. 💬 COMMUNICATE (Reply from Registry)")
        print("3. 📊 DASHBOARD (List All)")
        print("0. Exit")
        
        choice = input("\nSelect (0-3): ").strip()
        
        if choice == '0': break
        elif choice == '1': run_create_menu(registry, bridge)
        elif choice == '2': run_reply_menu(bridge, registry)
        elif choice == '3':
            os.system(f"python {BASE_DIR}/scripts/jules_bridge.py dashboard")
            input("\nPress Enter...")
        else:
            pass

if __name__ == "__main__":
    main()
