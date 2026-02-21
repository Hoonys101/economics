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
    "lane1-finance-recovery": {
        "title": "Lane 1 Implementation: Finance & M2 Hardening",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MISSION_lane1-finance_JULES_SPEC.md",
        "instruction": "Refactor ICurrencyHolder protocol, update WorldState M2 calculation logic, and ensure integer precision across the finance module as per spec.",
        "wait": True
    },
    "lane2-structural-recovery": {
        "title": "Lane 2 Implementation: Lifecycle & Saga Fix",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MISSION_lane2-structural_JULES_SPEC.md",
        "instruction": "Enforce registration-before-funding lifecycle in firm_management.py and unify Saga DTOs using SagaParticipantDTO in housing_api.py.",
        "wait": True
    },
    "lane3-dx-hardening": {
        "title": "Lane 3 Implementation: Orchestrator & Test Stabilization",
        "command": "create",
        "file": "design/3_work_artifacts/specs/MISSION_lane3-dx_JULES_SPEC.md",
        "instruction": "Harden TickOrchestrator attribute access and refactor failing Saga unit tests to use strict dataclass DTOs as per spec.",
        "wait": True
    }
}
