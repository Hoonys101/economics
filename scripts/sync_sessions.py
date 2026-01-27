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
    from jules_bridge import DEFAULT_SOURCE
    
    print(f"🔄 Fetching sessions for {DEFAULT_SOURCE} from server...")
    try:
        # Fetching raw sessions to inspect sourceContext
        all_sessions = bridge.list_sessions(page_size=50)
    except Exception as e:
        print(f"❌ API Error: {e}")
        return
    
    if not ASSIGNMENTS_PATH.exists():
        print("❌ team_assignments.json not found.")
        return

    with open(ASSIGNMENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "antigravity" not in data:
        data["antigravity"] = {"active_sessions": {}, "completed_sessions": {}}
    
    local_active = data["antigravity"].get("active_sessions", {})
    local_completed = data["antigravity"].get("completed_sessions", {})
    
    # Map server sessions by ID and filter by source
    server_map = {}
    for s in all_sessions:
        # API returns 'id' directly for summary, but raw might use 'name'
        sid = s.get("id") or s.get("name", "").split("/")[-1]
        
        # Source can be directly in 'source' or inside 'sourceContext'
        source_context = s.get("sourceContext")
        if isinstance(source_context, dict):
             source = source_context.get("source")
        else:
             source = s.get("source")
        
        if sid and source == DEFAULT_SOURCE:
            server_map[sid] = s
            # Ensure state is present
            if "state" not in server_map[sid]:
                server_map[sid]["state"] = s.get("state", "IN_PROGRESS")
    
    new_active = {}
    remaining_completed = {}
    
    print(f"📊 Analyzing local sessions vs {len(server_map)} matching server sessions...")

    # 1. Reconcile local active sessions with server
    for sid, info in local_active.items():
        if sid in server_map:
            session = server_map[sid]
            state = session.get("state", "IN_PROGRESS")
            
            if state in ["PLANNING", "IN_PROGRESS", "COMPLETED"]:
                new_active[sid] = info
                title = session.get("title") or info.get("title", "Untitled")
                if state == "COMPLETED" and "(COMPLETED)" not in title:
                    title = f"{title} (COMPLETED)"
                new_active[sid]["title"] = title
            else:
                print(f"✅ Session {sid} is {state}. Moving to history.")
                remaining_completed[sid] = f"{info.get('title', 'Unknown')} - {state} on Server"
        else:
            print(f"❓ Session {sid} not in recent list. Archiving locally.")
            remaining_completed[sid] = f"{info.get('title', 'Unknown')} - ARCHIVED_OR_OTHERS"

    # 2. Add/Recover sessions from server
    for sid, session in server_map.items():
        # Recover if it was accidentally moved to history or is new
        state = session.get("state", "IN_PROGRESS")
        if state in ["PLANNING", "IN_PROGRESS", "COMPLETED"]:
            if sid not in new_active:
                title = session.get("title") or "New Session"
                if state == "COMPLETED" and "(COMPLETED)" not in title:
                    title = f"{title} (COMPLETED)"
                
                print(f"✨ Syncing/Recovering session: {sid} ({title})")
                new_active[sid] = {
                    "title": title,
                    "initial_mission": "Synchronized from server"
                }

    # 3. Preserve other history that wasn't just moved
    for sid, info in local_completed.items():
        if sid not in new_active and sid not in remaining_completed:
            remaining_completed[sid] = info

    data["antigravity"]["active_sessions"] = new_active
    data["antigravity"]["completed_sessions"] = remaining_completed
    
    with open(ASSIGNMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Sync Complete.")
    print(f"   - Active/Communicable: {len(new_active)}")
    print(f"   - Stored History: {len(remaining_completed)}")

if __name__ == "__main__":
    sync()
