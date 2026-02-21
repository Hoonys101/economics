"""
🛠️ [ANTIGRAVITY] JULES MISSION MANIFEST GUIDE (Manual)
====================================================

1. POSITION & ROLE
   - 역할: 코드 구현, 버그 수정, 단위 테스트 작성 및 실행 (Coding).
   - 핵심 가치: "승인된 MISSION_spec을 실제 동작하는 코드로 정확히 구현한다."
   - [MANDATE]: DTO나 API가 변경되는 경우, 전수조사를 통해 모든 구현체에 변동을 반영한다.

3. FIELD SCHEMA (JULES_MISSIONS)
   - title (str): 구현 업무의 제목.
   - command (str, Optional): 실행할 명령 유형 (create, send-message, status, complete).
   - instruction (str): 구체적인 행동 지시. 'file' 미사용 시 필수.
   - file (str, Optional): MISSION_spec 또는 통합 미션 가이드 문서 경로.
   - wait (bool, Optional): 작업 완료까지 대기 여부. (기본값: False)
"""
from typing import Dict, Any

JULES_MISSIONS: Dict[str, Dict[str, Any]] = {
    "mod-finance-recovery": {
        "title": "Module A Fix: Finance & Accounting Integrity",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MOD_FINANCE_SPEC.md",
        "instruction": "Implement finance fixes. CRITICAL: Do NOT modify shared API/DTO files (e.g., simulation/dtos/api.py). If a contract change is needed, mark it as # TODO: TD-CONTRACT-SYNC and implement internally.",
        "wait": True
    },
    "mod-arch-recovery": {
        "title": "Module B Fix: Architecture & Orchestration",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MOD_ARCH_SPEC.md",
        "instruction": "Refactor architecture. CRITICAL: Do NOT modify shared API/DTO files. If a contract change is needed, mark it as # TODO: TD-CONTRACT-SYNC and implement internally.",
        "wait": True
    },
    "mod-lifecycle-recovery": {
        "title": "Module C Fix: Lifecycle & Saga Reliability",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MOD_LIFECYCLE_SPEC.md",
        "instruction": "Standardize lifecycle. CRITICAL: Do NOT modify shared API/DTO files. If a contract change is needed, mark it as # TODO: TD-CONTRACT-SYNC and implement internally.",
        "wait": True
    },
    "mod-test-recovery": {
        "title": "Module D Fix: Test Suite Modernization",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MOD_TEST_SPEC.md",
        "instruction": "Modernize test suite. CRITICAL: Do NOT modify shared API/DTO files. If a contract change is needed, mark it as # TODO: TD-CONTRACT-SYNC and implement internally.",
        "wait": True
    }
}
