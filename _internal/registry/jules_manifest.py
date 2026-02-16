"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST GUIDE (Manual)
====================================================

1. POSITION & ROLE
   - 역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
   - 핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."

3. FIELD SCHEMA (JULES_MISSIONS)
   - title (str): 구현 업무의 제목.
   - command (str, Optional): 실행할 명령 유형 (create, send-message, status, complete).
   - instruction (str): 구체적인 행동 지시. 'file' 미사용 시 필수.
   - file (str, Optional): MISSION_spec 또는 통합 미션 가이드 문서 경로.
   - wait (bool, Optional): 작업 완료까지 대기 여부. (기본값: False)
   - session_id (str, Optional): '장착'된 미션의 세션 ID.
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "build-phase-audit-system": {
        "description": "Create a diagnostic script that audits total money supply after every phase in TickOrchestrator to find leaks.",
        "instruction": "Create 'scripts/run_phase_audit.py'. This script must: 1. Initialize simulation. 2. Manually execute each phase of TickOrchestrator for Tick 1. 3. Output a table showing 'Total Assets' (HH+Firm+Gov+Bank) and the 'Delta' after each phase. 4. Save output to 'reports/temp/phase_audit.log'. Avoid using sim.run_tick(), orchestrate phases manually and handle sim_state sync."
    },
    "fix-and-run-diagnostics": {
        "title": "Forensic Execution: Repair and Run Leak Diagnostics",
        "command": "create",
        "instruction": "`scripts/diagnose_money_leak.py` 스크립트가 최신 엔진 코드(특히 `Bank` 클래스의 `.assets` 참조 오류)와 호환되도록 수정하고 실행하십시오. 실행 결과(Transaction Summary 포함)를 `reports/temp/tick1_diagnostics.log`로 저장하여 Gemini의 후속 분석을 위한 데이터를 확보하십시오.",
        "wait": True
    }
}
