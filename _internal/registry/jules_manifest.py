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
    "phase23-dto-core": {
        "worker": "coder",
        "instruction": "Execute Core DTO & Orchestration naming alignment as per PHASE23_DTO_ALIGNMENT_CORE.md. Update checklist after each file.",
        "integrated_mission_guide": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_CORE.md",
        "context_files": [
            "c:/coding/economics/simulation/dtos/api.py",
            "c:/coding/economics/simulation/world_state.py",
            "c:/coding/economics/simulation/orchestration/tick_orchestrator.py",
            "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_CORE.md"
        ]
    },
    "phase23-dto-modules": {
        "worker": "coder",
        "instruction": "Update business logic modules for DTO alignment as per PHASE23_DTO_ALIGNMENT_MODULES.md. Update checklist after each file.",
        "integrated_mission_guide": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_MODULES.md",
        "context_files": [
            "c:/coding/economics/modules/finance/system.py",
            "c:/coding/economics/modules/government/taxation/system.py",
            "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_MODULES.md"
        ]
    },
    "phase23-dto-tests": {
        "worker": "coder",
        "instruction": "Align test mocks with new SimulationState DTO fields as per PHASE23_DTO_ALIGNMENT_TESTS.md. Update checklist after each file.",
        "integrated_mission_guide": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_TESTS.md",
        "context_files": [
            "c:/coding/economics/tests/unit/systems/test_finance.py",
            "c:/coding/economics/tests/unit/agents/test_government.py",
            "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_TESTS.md"
        ]
    },
    "phase23-legacy-cleanup": {
        "worker": "coder",
        "instruction": "Cleanup legacy factories, protocols, and stale test logic as per PHASE23_LEGACY_CLEANUP.md. Update checklist after each file.",
        "integrated_mission_guide": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_LEGACY_CLEANUP.md",
        "context_files": [
            "c:/coding/economics/simulation/systems/demographic_manager.py",
            "c:/coding/economics/simulation/initialization/initializer.py",
            "c:/coding/economics/simulation/factories/agent_factory.py",
            "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_LEGACY_CLEANUP.md"
        ]
    }
}
