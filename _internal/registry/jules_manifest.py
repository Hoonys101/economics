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
    "exec-lifecycle-init-fix": {
        "title": "EXEC: Lifecycle Manager Initialization & Cycle Fix",
        "file": "design/3_work_artifacts/specs/MISSION_LIFECYCLE_INIT_FIX_SPEC.md",
        "instruction": "Follow MISSION_LIFECYCLE_INIT_FIX_SPEC.md: 1) Make household_factory mandatory in AgentLifecycleManager.__init__. 2) Update tests tests/unit/test_lifecycle_reset.py and tests/integration/test_wo167_grace_protocol.py to inject mock factories. 3) Ensure no circular imports.",
        "wait": False
    },
    "exec-trans-schema-migration": {
        "title": "EXEC: Transaction Schema Migration",
        "file": "design/4_hard_planning/FUTURE_LIQUIDATION_ROADMAP.md",
        "instruction": "Update simulation/models.py (Transaction) to include unit_price_pennies and total_pennies. Create a SQL migration script for the database backfill as specified in Wave 3.2.",
        "wait": False
    },
    "exec-test-modernization-fix": {
        "title": "EXEC: Full-Suite Test Modernization Fix",
        "file": "design/3_work_artifacts/specs/MISSION_TEST_MODERNIZATION_AUDIT_SPEC.md",
        "instruction": "Systematically modernize tests based on MISSION_TEST_MODERNIZATION_AUDIT_SPEC.md: 1) Inject IHouseholdFactory into all AgentLifecycleManager constructors. 2) Convert all USD dollar assertions to Penny integers in transaction/handler tests. 3) Update Housing tests to verify LienDTO structures. Focus on tests/unit and tests/integration.",
        "wait": False
    }
}
