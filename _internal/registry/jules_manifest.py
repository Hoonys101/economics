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
    "phase23-fix-household-integration-test": {
        "title": "Fix Household Integration Test",
        "instruction": "Hydrate Household wallet with initial liquidity and remove skip decorator as per the spec.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_phase23-fix-household-integration-test_SPEC.md"
    },
    "phase23-safety-net": {
        "title": "P1 Mission: Operation Safety Net",
        "instruction": "Restore test suite integrity by aligning mocks and lifecycle assumptions.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_phase23-spec-safety-net_SPEC.md"
    },
    "phase23-penny-perfect": {
        "title": "P2 Mission: Operation Penny Perfect",
        "instruction": "Enforce the Penny Standard (int) and add missing financial handlers.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_phase23-spec-penny-perfect_SPEC.md"
    },
    "phase23-surgical-separation": {
        "title": "P3 Mission: Operation Surgical Separation",
        "instruction": "Decouple Firm departments into stateless engines and fix WorldState singletons.",
        "file": "c:/coding/economics/design/3_work_artifacts/specs/MISSION_phase23-spec-surgical-separation_SPEC.md"
    }
}
