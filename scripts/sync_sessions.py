import json
import sys
import os
from pathlib import Path

# Add scripts dir to path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR / "scripts"))

try:
    from jules_bridge import JulesBridge
except ImportError:
    print("❌ Error: Could not import jules_bridge")
    sys.exit(1)

ASSIGNMENTS_PATH = BASE_DIR / "communications" / "team_assignments.json"

def sync():
    bridge = JulesBridge()
    print("🔄 Fetching sessions from server...")
    all_sessions = bridge.list_sessions()
    
    if not ASSIGNMENTS_PATH.exists():
        print("❌ team_assignments.json not found.")
        return

    with open(ASSIGNMENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "antigravity" not in data:
        data["antigravity"] = {"active_sessions": {}, "completed_sessions": {}}
    
    local_active = data["antigravity"].get("active_sessions", {})
    local_completed = data["antigravity"].get("completed_sessions", {})
    
    # Map server sessions by ID
    server_map = {s["id"]: s for s in all_sessions}
    
    new_active = {}
    
    print(f"📊 Analyzing {len(local_active)} local sessions and {len(all_sessions)} server sessions...")

    # 1. Check existing local active sessions
    for sid, info in local_active.items():
        if sid in server_map:
            session = server_map[sid]
            # If still active (not archived/finished), keep it
            status = session.get("status", "ACTIVE")
            if status not in ["ARCHIVED", "FINISHED"]:
                new_active[sid] = info
                # Update title if possible
                title = session.get("title")
                if title:
                    new_active[sid]["title"] = title
            else:
                print(f"✅ Session {sid} is {status}. Moving to completed.")
                local_completed[sid] = f"{info.get('title', 'Unknown')} - {status} on Server"
        else:
            # Not on server? Maybe deleted or too old. Move to completed/limbo
            print(f"❓ Session {sid} not found on server. Moving to completed/limbo.")
            local_completed[sid] = f"{info.get('title', 'Unknown')} - NOT_FOUND_ON_SERVER"

    # 2. Add new active sessions from server that aren't in local registry
    for sid, session in server_map.items():
        if sid not in local_active and sid not in local_completed:
            status = session.get("status", "ACTIVE")
            if status not in ["ARCHIVED", "FINISHED"]:
                print(f"✨ Found new active session on server: {sid} ({session.get('title', 'Untitled')})")
                new_active[sid] = {
                    "title": session.get("title") or "New Session",
                    "initial_mission": "Synchronized from server"
                }

    data["antigravity"]["active_sessions"] = new_active
    data["antigravity"]["completed_sessions"] = local_completed
    
    with open(ASSIGNMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"🎉 Sync Complete. Active: {len(new_active)}, Completed: {len(local_completed)}")

if __name__ == "__main__":
    sync()
