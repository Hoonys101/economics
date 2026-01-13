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

# Load .env file
try:
    from dotenv import load_dotenv
    # Find .env in project root
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on system env vars

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JulesBridge")

# Configuration
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
                # 가장 최근 활동이 에이전트 것이고, 이전 활동과 다르면 반환
                latest = activities[0]
                if latest.get("originator") == "agent" and latest.get("id") != last_act_id:
                    return latest
            
            time.sleep(3)
        
        logger.warning("Timed out waiting for agent response.")
        return None


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
    
    Args:
        task_description: What Jules should do.
        task_title: Short title for the task.
        work_order_path: Optional path to a Work Order file for context.
        
    Returns:
        JulesSession object.
    """
    bridge = JulesBridge()
    
    # If work order path provided, include it in the prompt
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
        session = bridge.create_session(prompt=prompt, title=title)
        print(f"Session created: {session.id}")
        print(f"Name: {session.name}")
    
    elif command == "status" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        status = check_jules_status(session_id)
        print(json.dumps(status, indent=2, default=str))
    
    elif command == "send-message" and len(sys.argv) >= 4:
        session_id = sys.argv[2]
        message = sys.argv[3]
        
        # 메시지 전송 전 최신 활동 ID 가져오기
        activities = bridge.list_activities(session_id, page_size=1)
        last_id = activities[0].get("id") if activities else None
        
        success = bridge.send_message(session_id, message)
        print(f"Message sent successfully to {session_id}")
        
        # --wait 옵션이 있거나 기본적으로 응답 대기 수행 (선택적)
        if "--wait" in sys.argv or True: # 일단 기본으로 대기하게 설정 (사용자 편의)
            response = bridge.wait_for_agent_response(session_id, last_act_id=last_id)
            if response:
                print("\n🤖 Jules Response:")
                progress = response.get("progressUpdated", {})
                print(f"Title: {progress.get('title')}")
                if progress.get('description'):
                    print(f"Description: {progress.get('description')}")
            else:
                print("\n⏳ No immediate response from agent (check activities later).")

    elif command == "activities" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        page_size = int(sys.argv[3]) if len(sys.argv) >= 4 else 30
        activities = bridge.list_activities(session_id, page_size=page_size)
        print(json.dumps(activities, indent=2, default=str))

    elif command == "approve-plan" and len(sys.argv) >= 3:
        session_id = sys.argv[2]
        success = bridge.approve_plan(session_id)
        print(f"Plan approved for {session_id}: {success}")
    
    else:
        print("Usage:")
        print("  python jules_bridge.py list-sources")
        print("  python jules_bridge.py list-sessions")
        print("  python jules_bridge.py create <title> <prompt>")
        print("  python jules_bridge.py status <session_id>")
        print("  python jules_bridge.py send-message <session_id> <message>")
        print("  python jules_bridge.py activities <session_id> [page_size]")
        print("  python jules_bridge.py approve-plan <session_id>")
        sys.exit(1)
