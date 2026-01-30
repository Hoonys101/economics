import os
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    insights_dir = Path("communications/insights")
    handover_dir = Path("design/_archive/handovers")
    handover_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    final_handover_path = handover_dir / f"HANDOVER_{timestamp}.md"
    
    # 1. Collect Insight Files
    if not insights_dir.exists():
        print(f"⚠️ Insights directory not found: {insights_dir}")
        insight_files = []
    else:
        insight_files = [str(insights_dir / f) for f in os.listdir(insights_dir) if f.endswith(".md")]

    if not insight_files:
        print("📭 No insight files found. Reporting based on session context only.")
    else:
        print(f"🔍 Found {len(insight_files)} insight files. Harvesting 지식...")

    # 2. Instruction for Gemini
    instruction = (
        "## 🏗️ Architectural Handover Report Generation\n"
        "당신은 수석 설계자에게 보고할 핸드오버 문서를 작성하는 리포터입니다.\n"
        "제공된 인사이트 문서들을 바탕으로 다음 사항을 요약하여 기록하십시오:\n"
        "1. **Accomplishments**: 이번 세션에서 완성된 핵심 기능 및 아키텍처 변화 (Animal Spirits 등).\n"
        "2. **Economic Insights**: 시뮬레이션 중 발견된 주요 경제적 통찰.\n"
        "3. **Pending Tasks & Tech Debt**: 다음 세션에서 즉시 해결해야 할 기술 부채 및 미완성 과제.\n"
        "4. **Verification Status**: `main.py` 및 `trace_leak.py` 등의 검증 결과 요약.\n\n"
        "결과물은 '설계도_계약들/HANDOVER.md' 형식을 따르되, 우리 프로젝트의 'design/HANDOVER.md' 위치에 저장될 예정입니다."
    )

    # 3. Arm Gemini Mission
    print("🤖 Arming Gemini for Handover Generation...")
    cmd = [
        "python", "scripts/cmd_ops.py", "set-gemini", "mission-session-handover",
        "--worker", "reporter",
        "--instruction", instruction
    ]
    if insight_files:
        cmd += ["--context"] + insight_files

    try:
        subprocess.run(cmd, check=True)
        # Execute armed mission
        print("🚀 Running Gemini Mission...")
        subprocess.run(["call", "gemini-go.bat", "mission-session-handover"], shell=True, check=True)
        print(f"✅ Handover Report Generated.")
    except Exception as e:
        print(f"❌ Error during session handover generation: {e}")

if __name__ == "__main__":
    main()
