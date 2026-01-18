"""
Jules API Bridge - Antigravity's Interface to Jules
Phase 23: AI Agent Orchestration

This script allows Antigravity to programmatically create Jules sessions,
monitor their progress, and retrieve results.
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent

# Load .env file
try:
    from dotenv import load_dotenv
    # Find .env in project root
    env_path = BASE_DIR / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on system env vars

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JulesBridge")

JULES_API_BASE = "https://jules.googleapis.com/v1alpha"
JULES_API_KEY = os.getenv("JULES_API_KEY")

# Default source (set this to your repo)
DEFAULT_SOURCE = "sources/github/Hoonys101/economics"


class AutomationMode(Enum):
    """Jules automation modes."""
    MANUAL = "MANUAL"  # No auto PR
    AUTO_CREATE_PR = "AUTO_CREATE_PR"  # Auto create PR on completion


@dataclass
class JulesSession:
    """Represents a Jules session."""
    id: str
    name: str
    title: str
    prompt: str
    source: str
    status: Optional[str] = None
    pr_url: Optional[str] = None


class JulesBridge:
    """
    Bridge between Antigravity and Jules API.
    Allows programmatic task assignment and monitoring.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or JULES_API_KEY
        if not self.api_key:
            raise ValueError("JULES_API_KEY not set. Add it to your .env file.")
        self.headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all available sources (connected repositories)."""
        response = requests.get(
            f"{JULES_API_BASE}/sources",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        return data.get("sources", [])

    def create_session(
        self,
        prompt: str,
        title: str,
        source: str = DEFAULT_SOURCE,
        starting_branch: str = "main",
        automation_mode: AutomationMode = AutomationMode.AUTO_CREATE_PR,
        require_plan_approval: bool = False
    ) -> JulesSession:
        """
        Create a new Jules session with the given task.
        
        Args:
            prompt: The task description for Jules.
            title: Session title (will be PR title if auto-created).
            source: Repository source name.
            starting_branch: Branch to base work on.
            automation_mode: Whether to auto-create PR.
            require_plan_approval: If True, waits for explicit approval.
            
        Returns:
            JulesSession object with session details.
        """
        if source != DEFAULT_SOURCE:
            # Safety Guard: Prevent accidental assignment to wrong project
            logger.warning(f"Target source '{source}' differs from default '{DEFAULT_SOURCE}'.")
            # For strict mode, we could raise an error here.
            # raise ValueError(f"Project Safety Guard: Cannot assign to external source '{source}'")
            
        payload = {
            "prompt": prompt,
            "title": title,
            "sourceContext": {
                "source": source,
                "githubRepoContext": {
                    "startingBranch": starting_branch
                }
            },
            "automationMode": automation_mode.value,
            "requirePlanApproval": require_plan_approval
        }

        logger.info(f"Creating Jules session: {title}")
        response = requests.post(
            f"{JULES_API_BASE}/sessions",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

        return JulesSession(
            id=data["id"],
            name=data["name"],
            title=data["title"],
            prompt=data["prompt"],
            source=source
        )

    def get_session(self, session_id: str, compact: bool = False) -> Dict[str, Any]:
        """Get details of a specific session. Use compact=True for minimal output."""
        response = requests.get(
            f"{JULES_API_BASE}/sessions/{session_id}",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        if compact:
            return {
                "id": data.get("id"),
                "title": data.get("title"),
                "state": data.get("state"),
                "updateTime": data.get("updateTime"),
                "pr_url": next((o["pullRequest"]["url"] for o in data.get("outputs", []) if "pullRequest" in o), None)
            }
        return data

    def list_sessions(self, page_size: int = 10, summary: bool = False) -> List[Dict[str, Any]]:
        """List recent sessions. Use summary=True for minimal output."""
        response = requests.get(
            f"{JULES_API_BASE}/sessions",
            headers=self.headers,
            params={"pageSize": page_size}
        )
        response.raise_for_status()
        sessions = response.json().get("sessions", [])
        if summary:
            return [{
                "id": s.get("id"),
                "title": s.get("title"),
                "state": s.get("state"),
                "updateTime": s.get("updateTime")
            } for s in sessions]
        return sessions

    def approve_plan(self, session_id: str) -> bool:
        """Approve the plan for a session that requires approval."""
        response = requests.post(
            f"{JULES_API_BASE}/sessions/{session_id}:approvePlan",
            headers=self.headers
        )
        response.raise_for_status()
        logger.info(f"Plan approved for session {session_id}")
        return True

    def send_message(self, session_id: str, message: str) -> bool:
        """Send a follow-up message to an active session."""
        payload = {"prompt": message}
        response = requests.post(
            f"{JULES_API_BASE}/sessions/{session_id}:sendMessage",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        logger.info(f"Message sent to session {session_id}")
        return True

    def list_activities(self, session_id: str, page_size: int = 30) -> List[Dict[str, Any]]:
        """List activities in a session."""
        response = requests.get(
            f"{JULES_API_BASE}/sessions/{session_id}/activities",
            headers=self.headers,
            params={"pageSize": page_size}
        )
        response.raise_for_status()
        return response.json().get("activities", [])

    def get_session_output(self, session_id: str) -> Optional[str]:
        """Check if session has completed and return PR URL if available."""
        session = self.get_session(session_id)
        outputs = session.get("outputs", [])
        for output in outputs:
            if "pullRequest" in output:
                return output["pullRequest"].get("url")
        return None

    def wait_for_agent_response(self, session_id: str, last_act_id: Optional[str] = None, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """메시지 전송 후 에이전트의 응답(Activity)이 올 때까지 대기"""
        import time
        start_time = time.time()
        logger.info(f"Waiting for agent response in session {session_id}...")
        
        while time.time() - start_time < timeout:
            activities = self.list_activities(session_id, page_size=5)
            if activities:
                latest = activities[0]
                if latest.get("originator") == "agent" and latest.get("id") != last_act_id:
                    return latest
            time.sleep(3)
        
        logger.warning("Timed out waiting for agent response.")
        return None

    def sync_git(self, title: str) -> bool:
        """
        Auto-push latest changes to ensure Jules gets fresh code.
        Returns True if successful.
        """
        import subprocess
        print(f"[GIT] Syncing Git changes for task: {title}...")
        try:
            # Check if there are changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            if status_result.stdout.strip():
                # There are uncommitted changes
                subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
                subprocess.run(
                    ["git", "commit", "-m", f"chore: Pre-Jules dispatch for {title}"],
                    cwd=BASE_DIR, check=True
                )
                print("   [x] Changes committed")
            else:
                print("   [i] No uncommitted changes")
            
            # Always push to ensure remote is up-to-date
            push_result = subprocess.run(
                ["git", "push"],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            if push_result.returncode == 0:
                print("   [x] Pushed to remote")
                return True
            else:
                print(f"   ⚠️ Push warning: {push_result.stderr.strip()}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ Git operation failed: {e}")
            return False
        except FileNotFoundError:
            print("   ⚠️ Git not found")
            return False


# =============================================================================
# Session Registry (team_assignments.json 자동 관리)
# =============================================================================

REGISTRY_PATH = BASE_DIR / "communications" / "team_assignments.json"

def _load_registry() -> Dict:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"antigravity": {"project": DEFAULT_SOURCE.split('/')[-1], "active_sessions": {}}}

def _save_registry(data: Dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def register_session(session_id: str, title: str, prompt: str = ""):
    """새 세션을 레지스트리에 등록 (초기 미션 포함)"""
    registry = _load_registry()
    registry.setdefault("antigravity", {}).setdefault("active_sessions", {})
    registry["antigravity"]["active_sessions"][session_id] = {
        "title": title,
        "initial_mission": prompt
    }
    _save_registry(registry)
    logger.info(f"Session registered: {session_id} - {title}")

def complete_session(session_id: str):
    """세션을 완료 상태로 마킹"""
    registry = _load_registry()
    sessions = registry.get("antigravity", {}).get("active_sessions", {})
    if session_id in sessions:
        entry = sessions[session_id]
        if isinstance(entry, dict):
            current_title = entry["title"]
            if "(COMPLETED)" not in current_title:
                entry["title"] = f"{current_title} (COMPLETED)"
        else:
            # Legacy support
            if "(COMPLETED)" not in entry:
                sessions[session_id] = f"{entry} (COMPLETED)"
        _save_registry(registry)
        logger.info(f"Session completed: {session_id}")

def get_my_sessions() -> Dict[str, str]:
    """현재 담당 세션 목록 반환 (토큰 절약)"""
    registry = _load_registry()
    return registry.get("antigravity", {}).get("active_sessions", {})

def archive_session(session_id: str):
    """완료된 세션을 레지스트리에서 제거"""
    registry = _load_registry()
    sessions = registry.get("antigravity", {}).get("active_sessions", {})
    if session_id in sessions:
        del sessions[session_id]
        _save_registry(registry)
        logger.info(f"Session archived: {session_id}")


# =============================================================================
# Convenience Functions for Antigravity
# =============================================================================

def assign_task_to_jules(
    task_description: str,
    task_title: str,
    work_order_path: Optional[str] = None
) -> JulesSession:
    """
    Assign a task to Jules with optional work order context.
    """
    bridge = JulesBridge()
    
    if work_order_path and os.path.exists(work_order_path):
        with open(work_order_path, 'r', encoding='utf-8') as f:
            work_order_content = f.read()
        full_prompt = f"""## Task
{task_description}

## Work Order Reference
{work_order_content}

## Instructions
- Read AGENTS.md for project conventions.
- Follow the work order strictly.
- Create tests for new functionality.
- Run `pytest` before submitting.
"""
    else:
        full_prompt = f"""## Task
{task_description}

## Instructions
- Read AGENTS.md for project conventions.
- Create tests for new functionality.
- Run `pytest` before submitting.
"""
    
    return bridge.create_session(
        prompt=full_prompt,
        title=task_title,
        automation_mode=AutomationMode.AUTO_CREATE_PR
    )


def check_jules_status(session_id: str) -> Dict[str, Any]:
    """Check the status of a Jules session."""
    bridge = JulesBridge()
    session = bridge.get_session(session_id)
    activities = bridge.list_activities(session_id, page_size=5)
    
    return {
        "session": session,
        "recent_activities": activities,
        "pr_url": bridge.get_session_output(session_id)
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python jules_bridge.py list-sources")
        print("  python jules_bridge.py list-sessions")
        print("  python jules_bridge.py create <title> <prompt>")
        print("  python jules_bridge.py sync-git <title>")
        print("  python jules_bridge.py status <session_id>")
        sys.exit(1)
    
    command = sys.argv[1]
    bridge = JulesBridge()
    
    if command == "list-sources":
        sources = bridge.list_sources()
        print(json.dumps(sources, indent=2))
    
    elif command == "list-sessions":
        use_summary = "--summary" in sys.argv
        limit = 10
        for arg in sys.argv:
            if arg.startswith("--limit="):
                limit = int(arg.split("=")[1])
        sessions = bridge.list_sessions(page_size=limit, summary=use_summary)
        print(json.dumps(sessions, indent=2))
    
    elif command == "create" and len(sys.argv) >= 4:
        title = sys.argv[2]
        prompt = sys.argv[3]
        
        # Auto-sync Git
        bridge.sync_git(title)
        
        session = bridge.create_session(prompt=prompt, title=title)
        register_session(session.id, title, prompt)  # 자동 등록 (Prompt 포함)
        print(f"   [x] Session created: {session.id}")
        print(f"   [x] Name: {session.name}")
        print(f"   [x] Registered to team_assignments.json with initial mission")

    elif command == "sync-git" and len(sys.argv) >= 3:
        title = sys.argv[2]
        bridge.sync_git(title)
    
    elif command == "status" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        verbose = "--verbose" in sys.argv
        
        status = check_jules_status(session_id)
        
        if verbose:
            print(json.dumps(status, indent=2, default=str))
        else:
            # Summary Mode (Token Efficient)
            sess = status.get("session", {})
            acts = status.get("recent_activities", [])
            pr = status.get("pr_url")
            
            print(f"\n[Session Status]: {sess.get('title')}")
            print(f"ID: {sess.get('id')}")
            print(f"State: {sess.get('state')}")
            if pr:
                print(f"   [PR]: {pr}")
            
            print("\n[Latest Activity]:")
            if acts:
                latest = acts[0]
                desc = latest.get("description", "No description")
                # Truncate description to save tokens
                if len(desc) > 200:
                    desc = desc[:197] + "..."
                print(f"   [{latest.get('createTime')}] {latest.get('type')}: {desc}")
            else:
                print("   (No activities recorded)")
            print("-" * 40)

    elif command == "send-message" and len(sys.argv) >= 4:
        session_id = sys.argv[2]
        message = sys.argv[3]
        
        # Support for file input via --file or -f
        if (message == "--file" or message == "-f") and len(sys.argv) >= 5:
            file_path = Path(sys.argv[4])
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    message = f.read()
            else:
                print(f"❌ Error: File not found: {file_path}")
                sys.exit(1)
        
        # Safety Check: Ensure we are not messaging a session from another project
        # (This relies on the registry or we could check session source if we fetched it)
        # For now, we assume if you have the ID, you know what you are doing, 
        # but let's at least warn if it's not in our local registry.
        registry = _load_registry()
        my_sessions = registry.get("antigravity", {}).get("active_sessions", {})
        if session_id not in my_sessions:
            print(f"⚠️ Warning: Session {session_id} is not in your local active registry. Proceeding anyway...")

        activities = bridge.list_activities(session_id, page_size=1)
        last_id = activities[0].get("id") if activities else None
        
        success = bridge.send_message(session_id, message)
        print(f"Message sent successfully to {session_id}")
        
        if "--wait" in sys.argv:
            response = bridge.wait_for_agent_response(session_id, last_act_id=last_id)
            if response:
                print("\n[Jules Response]:")
                progress = response.get("progressUpdated", {})
                print(f"Title: {progress.get('title')}")
                desc = progress.get('description', '')
                if desc:
                     print(f"Description: {desc[:500]}..." if len(desc) > 500 else f"Description: {desc}")
            else:
                print("\n[!] No immediate response from agent.")

    elif command == "activities" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        page_size = int(sys.argv[3]) if len(sys.argv) >= 4 and sys.argv[3].isdigit() else 5
        verbose = "--verbose" in sys.argv
        
        activities = bridge.list_activities(session_id, page_size=page_size)
        
        if verbose:
            print(json.dumps(activities, indent=2, default=str))
        else:
            print(f"\n[Recent Activities] ({len(activities)}):")
            for act in activities:
                desc = act.get("description", "")
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                print(f"   - [{act.get('type')}] {desc}")

    elif command == "approve-plan" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        success = bridge.approve_plan(session_id)
        print(f"Plan approved for {session_id}: {success}")
    
    elif command == "my-sessions":
        sessions = get_my_sessions()
        print(f"\n[Active Sessions] ({len(sessions)}):")
        for sid, entry in sessions.items():
            title = entry["title"] if isinstance(entry, dict) else entry
            if "(COMPLETED)" in title:
                print(f"   [x] {sid}: {title}")
            else:
                # Minimal info fetch
                try:
                    info = bridge.get_session(sid, compact=True)
                    state = info.get("state", "UNKNOWN")
                    pr = info.get("pr_url", "")
                    print(f"   [*] {sid}: {title} [{state}]" + (f" -> PR: {pr}" if pr else ""))
                except Exception:
                    print(f"   [?] {sid}: {title} [Fetch Failed]")

    elif command == "complete" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        complete_session(session_id)
        print(f"Session {session_id} marked as COMPLETED")

    elif command == "archive" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        archive_session(session_id)
        print(f"Session {session_id} archived")
    
    else:
        print("Usage:")
        print("  python jules_bridge.py list-sources")
        print("  python jules_bridge.py list-sessions --summary")
        print("  python jules_bridge.py create <title> <prompt>")
        print("  python jules_bridge.py status <session_id> [--verbose]")
        print("  python jules_bridge.py send-message <session_id> <message> [--wait]")
        print("  python jules_bridge.py activities <session_id> [limit] [--verbose]")
        print("  python jules_bridge.py my-sessions")
        sys.exit(1)
