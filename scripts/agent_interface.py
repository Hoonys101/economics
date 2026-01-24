import sys
import json
import os
from pathlib import Path
import subprocess

# Add scripts dir to path to import worker modules
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR / "scripts"))

try:
    from gemini_worker import BaseGeminiWorker, SpecDrafter, Reporter, GitReviewer, ContextManager, GitOperator, Validator
    from jules_bridge import JulesBridge, get_my_sessions, register_session, AutomationMode
except ImportError as e:
    print(f"❌ Critical Error: Could not import worker modules. {e}")
    sys.exit(1)

CONTEXT_FILE = BASE_DIR / "design" / "agent_context.json"

def load_context():
    if not CONTEXT_FILE.exists():
        print(f"⚠️ No context file found at {CONTEXT_FILE}")
        print("   Creates a blank template...")
        return {
            "instruction": "",
            "context_files": [],
            "title": "",
            "tool_hint": "gemini" 
        }
    
    try:
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(context):
    clear_screen()
    print("==================================================")
    print("   🤖 ANTIGRAVITY AGENT INTERFACE (v1.0)")
    print("==================================================")
    if context.get("title"):
        print(f"📝 Active Task: {context['title']}")
    print(f"📄 Context Files: {len(context.get('context_files', []))} loaded")
    print("--------------------------------------------------")
    print(f"💬 Instruction Preview:\n   {context.get('instruction', '')[:100]}...")
    print("==================================================\n")

def run_gemini_menu(context):
    while True:
        print("\n[💎 Gemini Operations]")
        print("1. Spec Drafter (Draft Specs)")
        print("2. Auditor (Analyze & Critique)")
        print("3. Reporter (General Report)")
        print("4. Validator (Arch Check)")
        print("5. Git Reviewer (Code Review)")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect Worker (0-5): ").strip()
        
        worker = None
        if choice == '0': return
        elif choice == '1': worker = SpecDrafter()
        elif choice == '2': worker = Reporter() # Auditor uses Reporter logic
        elif choice == '3': worker = Reporter()
        elif choice == '4': worker = Validator()
        elif choice == '5': worker = GitReviewer()
        else:
            print("❌ Invalid selection")
            continue
            
        if worker:
            print(f"\n🚀 Launching Gemini ({choice})...")
            try:
                # Use context from JSON
                worker.execute(
                    instruction=context["instruction"],
                    context_files=context.get("context_files", [])
                )
                input("\n✅ Job Done. Press Enter to continue...")
                return
            except Exception as e:
                print(f"❌ Execution Failed: {e}")
                input("Press Enter to continue...")

def run_jules_menu(context):
    bridge = JulesBridge()
    
    while True:
        print("\n[⚡ Jules Operations]")
        print("1. CREATE New Session")
        print("2. REPLY to Active Session")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect Mode (0-2): ").strip()
        
        if choice == '0': return
        
        elif choice == '1': # Create
            title = context.get("title") or input("Enter Task Title: ")
            
            # Auto-sync Git
            print("\n🔄 Syncing Git before dispatch...")
            bridge.sync_git(title)
            
            print(f"\n🚀 Dispatching Jules: {title}")
            try:
                session = bridge.create_session(
                    prompt=context["instruction"],
                    title=title,
                    automation_mode=AutomationMode.AUTO_CREATE_PR
                )
                # Register locally
                register_session(session.id, title, context["instruction"])
                
                print(f"\n✅ Session Created!")
                print(f"   ID: {session.id}")
                print(f"   Visit: https://idx.google.com/ (Jules Panel)")
                input("\nPress Enter to return...")
                return
            except Exception as e:
                print(f"❌ Failed to create session: {e}")
        
        elif choice == '2': # Reply
            sessions = get_my_sessions()
            if not sessions:
                print("⚠️ No active sessions found in team_assignments.json")
                continue
            
            valid_sessions = []
            print("\n📋 Active Sessions:")
            idx = 1
            for sid, data in sessions.items():
                # Filter out completed if needed, but sometimes we reply to completed to reopen
                title = data if isinstance(data, str) else data.get("title", "Unknown")
                print(f"   {idx}. {title} ({sid})")
                valid_sessions.append(sid)
                idx += 1
            
            sel = input("\nSelect Session Number: ").strip()
            if not sel.isdigit() or int(sel) < 1 or int(sel) > len(valid_sessions):
                print("❌ Invalid selection")
                continue
                
            target_sid = valid_sessions[int(sel)-1]
            
            # For reply, we usually send an updated instruction OR the one in context
            # Checking if user wants to use the context instruction or type a quick one
            print("\n--- Message Content ---")
            print("1. Use Instruction from agent_context.json")
            print("2. Type a quick message now")
            
            msg_choice = input("Select (1-2): ").strip()
            message = ""
            
            if msg_choice == '1':
                message = context["instruction"]
            elif msg_choice == '2':
                message = input("Enter message: ")
            else:
                continue
                
            if not message:
                print("❌ Empty message. Aborting.")
                continue
                
            print(f"\n🚀 Sending to {target_sid}...")
            try:
                bridge.send_message(target_sid, message)
                print("\n✅ Message Sent! Waiting for Jules...")
                
                # Optional wait
                do_wait = input("Wait for response? (y/n): ").lower() == 'y'
                if do_wait:
                    resp = bridge.wait_for_agent_response(target_sid)
                    if resp:
                        print(f"\n🤖 Jules Says: {resp.get('description', '')[:200]}...")
                
                input("\nPress Enter to return...")
                return
            except Exception as e:
                print(f"❌ Failed to send message: {e}")


def main():
    while True:
        context = load_context()
        if not context:
            input("Press Enter to Exit...")
            break
            
        print_header(context)
        
        print("1. Run with GEMINI (Analysis/Design)")
        print("2. Run with JULES (Coding/Implementation)")
        print("R. Reload Context File")
        print("Q. Quit")
        
        main_choice = input("\nSelect Agent (1, 2, R, Q): ").strip().upper()
        
        if main_choice == '1':
            run_gemini_menu(context)
        elif main_choice == '2':
            run_jules_menu(context)
        elif main_choice == 'R':
            continue
        elif main_choice == 'Q':
            print("Bye!")
            sys.exit(0)
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
