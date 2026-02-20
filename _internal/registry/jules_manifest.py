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
        "title": "Phase 23 DTO Core Alignment",
        "instruction": "Execute naming alignment for DTOs and Orchestrator as per the spec file.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_CORE.md"
    },
    "phase23-dto-modules": {
        "title": "Phase 23 DTO Module Alignment",
        "instruction": "Update module-level government references as per the spec file.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_MODULES.md"
    },
    "phase23-dto-tests": {
        "title": "Phase 23 DTO Test Alignment",
        "instruction": "Modernize test mocks for SimulationState parity as per the spec file.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_DTO_ALIGNMENT_TESTS.md"
    },
    "phase23-legacy-cleanup": {
        "title": "Phase 23 Legacy API Cleanup",
        "instruction": "Remove deprecated factories and stale lifecycle calls as per the spec file.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/PHASE23_LEGACY_CLEANUP.md"
    }
}
