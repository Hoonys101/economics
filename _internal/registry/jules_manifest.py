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
    "liquidate-residual": {
        "title": "Liquidate Residual Failures (Welfare, Sales, Finance)",
        "file": "design/3_work_artifacts/specs/MISSION_liquidate-residual-implementation_SPEC.md",
        "instruction": "Implement the specific fixes detailed in the spec for WelfareService, SalesEngine, and FinanceEngine. Ensure all Dollar-vs-Penny drift is eliminated by using strict integer casting. Verify with unit tests provided in the spec."
    },
    "market-precision-refactor": {
        "title": "Market Precision Refactor (Matching Engine)",
        "file": "design/3_work_artifacts/specs/MISSION_market-precision-refactor_SPEC.md",
        "instruction": "Refactor CanonicalOrderDTO and the MatchingEngine to use strict Integer Math (pennies). Implement integer mid-price calculation and Zero-Sum settlement as specified. Ensure M2 integrity is preserved."
    },
    "protocol-lockdown": {
        "title": "Phase 15 Architectural Protocol Lockdown",
        "file": "design/3_work_artifacts/specs/MISSION_protocol-lockdown-implementation_SPEC.md",
        "instruction": "Build the Architect's Hammer: A static analysis tool to enforce SEO patterns and block private attribute leaks as defined in the spec. Implement the core scanner and the three rules (SEO-001, DTO-001, FIN-001)."
    },
    "lifecycle-decomposition": {
        "title": "Lifecycle Manager Decomposition",
        "file": "design/3_work_artifacts/specs/MISSION_lifecycle-decomposition-implementation_SPEC.md",
        "instruction": "Implement the structural decomposition of LifecycleManager into BirthSystem, DeathSystem, and AgingSystem. Ensure the coordinator in LifecycleManager correctly delegates tasks. Verify with split unit tests for each sub-system."
    },
    "transaction-unification": {
        "title": "Transaction Logic Unification",
        "file": "design/3_work_artifacts/specs/MISSION_transaction-unification-implementation_SPEC.md",
        "instruction": "Deprecate TransactionManager and migrate all logic to TransactionProcessor. Redirect all callers (markets, modules) to the new processor. Ensure zero-sum integrity and anti-fraud checks are preserved."
    },
    "resolve-post-merge-import-errors": {
        "title": "Post-Merge Import & Path Stabilization",
        "file": "design/3_work_artifacts/specs/MISSION_resolve-import-errors_SPEC.md",
        "instruction": "Audit the test suite for all broken imports and file path errors resulting from the recent merge. Fix all ImportErrors and ensure parity between updated DTOs and their consumers."
    }
}
