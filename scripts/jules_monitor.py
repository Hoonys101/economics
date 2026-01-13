#!/usr/bin/env python3
"""
Jules Monitor - Jules 세션 상태를 주기적으로 모니터링하고 알림

사용법:
    python scripts/jules_monitor.py                    # 기본 5분 간격
    python scripts/jules_monitor.py --interval 60     # 1분 간격
    python scripts/jules_monitor.py --once            # 한 번만 체크
    python scripts/jules_monitor.py --watch <id>      # 특정 세션만 감시

알림 조건:
    - 새 PR 생성
    - 세션 완료
    - Jules가 질문/피드백 요청
    - 오류 발생
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

# Jules Bridge 임포트
from jules_bridge import JulesBridge, JULES_API_KEY

# Windows 토스트 알림
try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False
    print("⚠️ win10toast 미설치. pip install win10toast 로 설치하면 팝업 알림 가능")


class JulesMonitor:
    """Jules 세션 모니터"""
    
    def __init__(self, bridge: JulesBridge):
        self.bridge = bridge
        self.toaster = ToastNotifier() if TOAST_AVAILABLE else None
        self.known_sessions: Set[str] = set()
        self.known_prs: Set[str] = set()
        self.known_activities: Dict[str, Set[str]] = {}  # session_id -> activity_ids
        self.log_file = Path(__file__).parent.parent / "logs" / "jules_monitor.log"
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    
    def notify(self, title: str, message: str, duration: int = 10):
        """Windows 토스트 알림"""
        self.log(f"📢 NOTIFY: {title} - {message}")
        
        if self.toaster:
            try:
                self.toaster.show_toast(
                    title=f"🤖 Jules: {title}",
                    msg=message[:256],  # 토스트 메시지 길이 제한
                    duration=duration,
                    threaded=True
                )
            except Exception as e:
                self.log(f"Toast error: {e}", "ERROR")
    
    def check_sessions(self) -> List[Dict]:
        """모든 세션 체크"""
        try:
            sessions = self.bridge.list_sessions(page_size=20)
            events = []
            
            for session in sessions:
                # 필터링: 'economics' 저장소 관련 세션만 처리
                source_name = session.get("sourceContext", {}).get("source", "")
                if "economics" not in source_name.lower():
                    continue

                session_id = session.get("id")
                session_name = session.get("title", "Untitled")
                
                # 새 세션 감지
                if session_id not in self.known_sessions:
                    self.known_sessions.add(session_id)
                    self.known_activities[session_id] = set()
                    events.append({
                        "type": "NEW_SESSION",
                        "session_id": session_id,
                        "title": session_name
                    })
                
                # PR 생성 감지
                outputs = session.get("outputs", [])
                for out in outputs:
                    if "pullRequest" in out:
                        pr_url = out["pullRequest"].get("url")
                        if pr_url and pr_url not in self.known_prs:
                            self.known_prs.add(pr_url)
                            events.append({
                                "type": "PR_CREATED",
                                "session_id": session_id,
                                "title": session_name,
                                "pr_url": pr_url
                            })
                
                # 활동 체크 (질문, 완료 등)
                activity_events = self.check_activities(session_id, session_name)
                events.extend(activity_events)
            
            return events
            
        except Exception as e:
            self.log(f"Session check failed: {e}", "ERROR")
            return []
    
    def check_activities(self, session_id: str, session_name: str) -> List[Dict]:
        """세션의 활동 체크"""
        events = []
        
        try:
            activities = self.bridge.list_activities(session_id, page_size=10)
            
            for act in activities:
                act_id = act.get("id")
                if act_id in self.known_activities.get(session_id, set()):
                    continue
                
                self.known_activities.setdefault(session_id, set()).add(act_id)
                
                # 세션 완료 감지
                if "sessionCompleted" in act:
                    events.append({
                        "type": "SESSION_COMPLETED",
                        "session_id": session_id,
                        "title": session_name
                    })
                
                # 질문/피드백 요청 감지 (agent가 보낸 메시지 중 특정 패턴)
                if act.get("originator") == "agent":
                    progress = act.get("progressUpdated", {})
                    title = progress.get("title", "")
                    desc = progress.get("description", "")
                    
                    # 질문 패턴 감지
                    question_keywords = ["question", "clarify", "confirm", "?", "질문", "확인"]
                    if any(kw in (title + desc).lower() for kw in question_keywords):
                        events.append({
                            "type": "QUESTION",
                            "session_id": session_id,
                            "title": session_name,
                            "message": title[:100]
                        })
                    
                    # 오류 감지
                    if "error" in (title + desc).lower() or "failed" in (title + desc).lower():
                        events.append({
                            "type": "ERROR",
                            "session_id": session_id,
                            "title": session_name,
                            "message": title[:100]
                        })
        
        except Exception as e:
            self.log(f"Activity check failed for {session_id}: {e}", "ERROR")
        
        return events
    
    def process_events(self, events: List[Dict]):
        """이벤트 처리 및 알림"""
        for event in events:
            event_type = event.get("type")
            session_name = event.get("title", "Unknown")
            
            if event_type == "NEW_SESSION":
                self.log(f"🆕 New session: {session_name}")
            
            elif event_type == "PR_CREATED":
                pr_url = event.get("pr_url")
                self.notify(
                    "PR 생성됨!",
                    f"{session_name}\n{pr_url}"
                )
            
            elif event_type == "SESSION_COMPLETED":
                self.notify(
                    "작업 완료!",
                    f"{session_name} 세션이 완료되었습니다."
                )
            
            elif event_type == "QUESTION":
                self.notify(
                    "질문 있음!",
                    f"{session_name}: {event.get('message', '')}"
                )
            
            elif event_type == "ERROR":
                self.notify(
                    "⚠️ 오류 발생!",
                    f"{session_name}: {event.get('message', '')}"
                )
    
    def run_once(self):
        """한 번 체크"""
        self.log("🔍 Checking Jules sessions...")
        events = self.check_sessions()
        self.process_events(events)
        self.log(f"✅ Check complete. {len(events)} events found.")
        return events
    
    def run_loop(self, interval: int = 300):
        """주기적 체크 루프"""
        self.log(f"🚀 Starting Jules Monitor (interval: {interval}s)")
        self.log(f"📁 Log file: {self.log_file}")
        
        # 초기 상태 수집 (알림 없이)
        try:
            sessions = self.bridge.list_sessions(page_size=20)
            for s in sessions:
                sid = s.get("id")
                self.known_sessions.add(sid)
                self.known_activities[sid] = set()
                
                # 기존 PR 수집
                for out in s.get("outputs", []):
                    if "pullRequest" in out:
                        self.known_prs.add(out["pullRequest"].get("url"))
                
                # 기존 활동 수집
                try:
                    activities = self.bridge.list_activities(sid, page_size=50)
                    for act in activities:
                        self.known_activities[sid].add(act.get("id"))
                except:
                    pass
            
            self.log(f"📊 Initial state: {len(self.known_sessions)} sessions, {len(self.known_prs)} PRs")
        except Exception as e:
            self.log(f"Initial state collection failed: {e}", "ERROR")
        
        # 모니터링 루프
        while True:
            try:
                events = self.check_sessions()
                self.process_events(events)
                
                if events:
                    self.log(f"📬 {len(events)} new events processed")
                
            except KeyboardInterrupt:
                self.log("🛑 Monitor stopped by user")
                break
            except Exception as e:
                self.log(f"Monitor error: {e}", "ERROR")
            
            time.sleep(interval)
    
    def watch_session(self, session_id: str, interval: int = 30):
        """특정 세션 집중 감시"""
        self.log(f"👁️ Watching session: {session_id}")
        
        self.known_activities[session_id] = set()
        
        while True:
            try:
                session = self.bridge.get_session(session_id)
                session_name = session.get("title", "Unknown")
                
                # PR 체크
                for out in session.get("outputs", []):
                    if "pullRequest" in out:
                        pr_url = out["pullRequest"].get("url")
                        if pr_url and pr_url not in self.known_prs:
                            self.known_prs.add(pr_url)
                            self.notify("PR 생성됨!", f"{session_name}\n{pr_url}")
                
                # 활동 체크
                events = self.check_activities(session_id, session_name)
                self.process_events(events)
                
                # 완료 체크
                for event in events:
                    if event.get("type") == "SESSION_COMPLETED":
                        self.log("✅ Session completed. Stopping watch.")
                        return
                
            except KeyboardInterrupt:
                self.log("🛑 Watch stopped by user")
                break
            except Exception as e:
                self.log(f"Watch error: {e}", "ERROR")
            
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Jules Session Monitor")
    parser.add_argument("--interval", "-i", type=int, default=300, help="체크 간격 (초, 기본: 300)")
    parser.add_argument("--once", action="store_true", help="한 번만 체크")
    parser.add_argument("--watch", "-w", help="특정 세션 ID 감시")
    
    args = parser.parse_args()
    
    if not JULES_API_KEY:
        print("❌ Error: JULES_API_KEY 환경변수를 설정해주세요.")
        sys.exit(1)
    
    bridge = JulesBridge(JULES_API_KEY)
    monitor = JulesMonitor(bridge)
    
    if args.once:
        monitor.run_once()
    elif args.watch:
        monitor.watch_session(args.watch, interval=min(args.interval, 60))
    else:
        monitor.run_loop(interval=args.interval)


if __name__ == "__main__":
    main()
