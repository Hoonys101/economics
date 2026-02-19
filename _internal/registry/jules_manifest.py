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
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "fix-mock-regressions": {
        "title": "Fix Mock Attribute Regressions (Cockpit 2.0)",
        "command": "create",
        "instruction": (
            "Fix the deprecated `system_command_queue` attribute in WorldState mocks based on the audit report.\n\n"
            "**Target Files:**\n"
            "1. `tests/orchestration/test_state_synchronization.py`\n"
            "2. `tests/modules/governance/test_cockpit_flow.py`\n"
            "3. `tests/integration/test_tick_normalization.py`\n"
            "4. `tests/integration/test_cockpit_integration.py`\n\n"
            "**Required Changes:**\n"
            "- Rename `ws.system_command_queue` (or `state.system_command_queue`) to `ws.system_commands` (or `state.system_commands`).\n"
            "- Ensure `system_commands` is initialized as a `list` (`[]`), NOT a `deque`.\n"
            "- Verify `god_command_queue` usage is consistent with `WorldState` (should be `deque`).\n"
            "- Fix unrelated `AttributeError` in `tests/system/test_engine.py` (AgentLifecycleManager) by invoking the correct DeathSystem or LiquidationManager method if possible.\n"
            "- Run the specific tests to verify fixes.\n\n"
            "**Reference:**\n"
            "- `design/3_work_artifacts/reports/AUDIT_MOCK_REGRESSIONS.md` (Audit Report)\n"
            "- `simulation/world_state.py` (Source of Truth)"
        ),
        "file": "design/3_work_artifacts/reports/AUDIT_MOCK_REGRESSIONS.md",
        "wait": True
    },
}
