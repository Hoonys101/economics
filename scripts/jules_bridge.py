#!/usr/bin/env python3
"""
Jules API Bridge - Antigravity와 Jules 연동을 위한 브릿지 스크립트

사용법:
    python scripts/jules_bridge.py list-sources
    python scripts/jules_bridge.py create-session --prompt "Fix the bug" --branch main
    python scripts/jules_bridge.py list-sessions
    python scripts/jules_bridge.py get-session <session_id>
    python scripts/jules_bridge.py approve-plan <session_id>
    python scripts/jules_bridge.py send-message <session_id> --message "Make it corgi themed"
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

JULES_API_BASE_URL = "https://jules.googleapis.com/v1alpha"
JULES_API_KEY = os.environ.get("JULES_API_KEY")

# 기본 저장소 설정 (환경변수 또는 하드코딩)
DEFAULT_REPO_OWNER = "Hoonys101"
DEFAULT_REPO_NAME = "economics"


@dataclass
class JulesSession:
    """Jules 세션 정보"""
    id: str
    name: str
    title: str
    prompt: str
    source: str
    outputs: list = None


class JulesBridge:
    """Jules API 클라이언트"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("JULES_API_KEY 환경변수가 설정되지 않았습니다.")
        self.api_key = api_key
        self.headers = {
            "X-Goog-Api-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """API 요청 실행"""
        url = f"{JULES_API_BASE_URL}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.text else {}
        
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            raise
    
    # ========================================================================
    # Sources
    # ========================================================================
    
    def list_sources(self) -> list:
        """연결된 소스(GitHub 저장소) 목록 조회"""
        result = self._request("GET", "sources")
        return result.get("sources", [])
    
    def get_source_name(self, owner: str = DEFAULT_REPO_OWNER, repo: str = DEFAULT_REPO_NAME) -> str:
        """특정 저장소의 source name 반환"""
        sources = self.list_sources()
        for source in sources:
            gh = source.get("githubRepo", {})
            if gh.get("owner") == owner and gh.get("repo") == repo:
                return source.get("name")
        return f"sources/github/{owner}/{repo}"
    
    # ========================================================================
    # Sessions
    # ========================================================================
    
    def create_session(
        self,
        prompt: str,
        title: Optional[str] = None,
        branch: str = "main",
        auto_create_pr: bool = True,
        require_plan_approval: bool = False,
        owner: str = DEFAULT_REPO_OWNER,
        repo: str = DEFAULT_REPO_NAME
    ) -> Dict[str, Any]:
        """새 Jules 세션 생성"""
        source_name = self.get_source_name(owner, repo)
        
        payload = {
            "prompt": prompt,
            "sourceContext": {
                "source": source_name,
                "githubRepoContext": {
                    "startingBranch": branch
                }
            },
            "title": title or f"Auto: {prompt[:50]}..."
        }
        
        if auto_create_pr:
            payload["automationMode"] = "AUTO_CREATE_PR"
        
        if require_plan_approval:
            payload["requirePlanApproval"] = True
        
        return self._request("POST", "sessions", payload)
    
    def list_sessions(self, page_size: int = 10) -> list:
        """세션 목록 조회"""
        result = self._request("GET", f"sessions?pageSize={page_size}")
        return result.get("sessions", [])
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """특정 세션 상세 조회"""
        return self._request("GET", f"sessions/{session_id}")
    
    def approve_plan(self, session_id: str) -> Dict[str, Any]:
        """세션의 계획 승인"""
        return self._request("POST", f"sessions/{session_id}:approvePlan", {})
    
    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """세션에 메시지 전송"""
        return self._request("POST", f"sessions/{session_id}:sendMessage", {"prompt": message})
    
    # ========================================================================
    # Activities
    # ========================================================================
    
    def list_activities(self, session_id: str, page_size: int = 30) -> list:
        """세션의 활동 목록 조회"""
        result = self._request("GET", f"sessions/{session_id}/activities?pageSize={page_size}")
        return result.get("activities", [])


# ============================================================================
# CLI Commands
# ============================================================================

def cmd_list_sources(bridge: JulesBridge, args):
    """소스 목록 출력"""
    sources = bridge.list_sources()
    print("\n📦 Connected Sources:")
    for source in sources:
        gh = source.get("githubRepo", {})
        print(f"  - {source.get('name')}")
        print(f"    Owner: {gh.get('owner')}, Repo: {gh.get('repo')}")
    print()


def cmd_create_session(bridge: JulesBridge, args):
    """새 세션 생성"""
    session = bridge.create_session(
        prompt=args.prompt,
        title=args.title,
        branch=args.branch,
        auto_create_pr=not args.no_pr,
        require_plan_approval=args.require_approval
    )
    
    print("\n✅ Session Created:")
    print(f"  ID: {session.get('id')}")
    print(f"  Name: {session.get('name')}")
    print(f"  Title: {session.get('title')}")
    print(f"  Prompt: {session.get('prompt')}")
    print()


def cmd_list_sessions(bridge: JulesBridge, args):
    """세션 목록 출력"""
    sessions = bridge.list_sessions(page_size=args.limit)
    print(f"\n📋 Recent Sessions ({len(sessions)}):")
    for s in sessions:
        outputs = s.get("outputs", [])
        pr_url = None
        for out in outputs:
            if "pullRequest" in out:
                pr_url = out["pullRequest"].get("url")
        
        print(f"  [{s.get('id')}] {s.get('title')}")
        if pr_url:
            print(f"      PR: {pr_url}")
    print()


def cmd_get_session(bridge: JulesBridge, args):
    """세션 상세 조회"""
    session = bridge.get_session(args.session_id)
    print(f"\n📄 Session Details:")
    print(json.dumps(session, indent=2, ensure_ascii=False))
    print()


def cmd_approve_plan(bridge: JulesBridge, args):
    """계획 승인"""
    bridge.approve_plan(args.session_id)
    print(f"\n✅ Plan approved for session: {args.session_id}")
    print()


def cmd_send_message(bridge: JulesBridge, args):
    """메시지 전송"""
    bridge.send_message(args.session_id, args.message)
    print(f"\n✅ Message sent to session: {args.session_id}")
    print(f"   Message: {args.message}")
    print()


def cmd_list_activities(bridge: JulesBridge, args):
    """활동 목록 조회"""
    activities = bridge.list_activities(args.session_id, page_size=args.limit)
    print(f"\n📊 Activities for Session {args.session_id}:")
    for act in activities:
        originator = act.get("originator", "unknown")
        create_time = act.get("createTime", "")
        
        # 활동 유형 판별
        if "planGenerated" in act:
            activity_type = "Plan Generated"
        elif "planApproved" in act:
            activity_type = "Plan Approved"
        elif "progressUpdated" in act:
            activity_type = act.get("progressUpdated", {}).get("title", "Progress")
        elif "sessionCompleted" in act:
            activity_type = "Session Completed"
        else:
            activity_type = "Other"
        
        print(f"  [{originator}] {activity_type} @ {create_time[:19] if create_time else 'N/A'}")
    print()


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Jules API Bridge - Antigravity와 Jules 연동",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # list-sources
    subparsers.add_parser("list-sources", help="연결된 GitHub 저장소 목록 조회")
    
    # create-session
    p_create = subparsers.add_parser("create-session", help="새 Jules 세션 생성")
    p_create.add_argument("--prompt", "-p", required=True, help="작업 프롬프트")
    p_create.add_argument("--title", "-t", help="세션 제목")
    p_create.add_argument("--branch", "-b", default="main", help="시작 브랜치 (default: main)")
    p_create.add_argument("--no-pr", action="store_true", help="자동 PR 생성 비활성화")
    p_create.add_argument("--require-approval", action="store_true", help="계획 승인 필요")
    
    # list-sessions
    p_list = subparsers.add_parser("list-sessions", help="세션 목록 조회")
    p_list.add_argument("--limit", "-l", type=int, default=10, help="조회할 세션 수")
    
    # get-session
    p_get = subparsers.add_parser("get-session", help="세션 상세 조회")
    p_get.add_argument("session_id", help="세션 ID")
    
    # approve-plan
    p_approve = subparsers.add_parser("approve-plan", help="계획 승인")
    p_approve.add_argument("session_id", help="세션 ID")
    
    # send-message
    p_msg = subparsers.add_parser("send-message", help="세션에 메시지 전송")
    p_msg.add_argument("session_id", help="세션 ID")
    p_msg.add_argument("--message", "-m", required=True, help="전송할 메시지")
    
    # list-activities
    p_acts = subparsers.add_parser("list-activities", help="세션 활동 목록 조회")
    p_acts.add_argument("session_id", help="세션 ID")
    p_acts.add_argument("--limit", "-l", type=int, default=30, help="조회할 활동 수")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # API Key 확인
    if not JULES_API_KEY:
        print("❌ Error: JULES_API_KEY 환경변수를 설정해주세요.")
        print("   예: set JULES_API_KEY=your_api_key_here")
        sys.exit(1)
    
    bridge = JulesBridge(JULES_API_KEY)
    
    # 명령어 실행
    commands = {
        "list-sources": cmd_list_sources,
        "create-session": cmd_create_session,
        "list-sessions": cmd_list_sessions,
        "get-session": cmd_get_session,
        "approve-plan": cmd_approve_plan,
        "send-message": cmd_send_message,
        "list-activities": cmd_list_activities,
    }
    
    if args.command in commands:
        commands[args.command](bridge, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
