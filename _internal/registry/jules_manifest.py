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
    "forensics_hardening_phase2": {
        "title": "Forensics Logic Stabilization (Wave 6)",
        "instruction": "Fix core structural logic identified in implementation_plan_wave6.md. Target: Eliminate 'Destination account does not exist' for new firms, register education_spending, and prevent NULL seller IDs in Sagas.",
        "file": "C:/Users/Gram Pro/.gemini/antigravity/brain/967802e0-ce79-47d5-bd15-774145a9ebae/implementation_plan_wave6.md"
    },
    "MISSION_finance_api_dto": {
        "title": "Finance Module API & DTO Realignment",
        "instruction": "Complete transition to strict @dataclass and ensure penny-standard enforcement. Harden SettlementSystem and Ledger integration as per SPEC.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_finance_api_dto_SPEC.md"
    },
    "MISSION_government_api_dto": {
        "title": "Government Module API & DTO Realignment",
        "instruction": "Optimize Policy/Tax API and integrate hyper-inflation fix. Align TreasuryDTO for bond orchestration.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_government_api_dto_SPEC.md"
    },
    "MISSION_firm_api_dto": {
        "title": "Firm Module API & DTO Realignment",
        "instruction": "Align FirmStateDTO/FirmConfigDTO. Add inventory/liability fields. Hardcode FirmFactory usage for atomicity.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_firm_api_dto_SPEC.md"
    },
    "MISSION_household_api_dto": {
        "title": "Household Module API & DTO Realignment",
        "instruction": "Implement Snapshot-based communication. Refactor consumption logic to return DTOs. Enforce assets_pennies SSoT.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_household_api_dto_SPEC.md"
    },
    "MISSION_labor_api_dto": {
        "title": "Labor Module API & DTO Realignment",
        "instruction": "Decouple MatchingEngine from agent attributes. Standardize JobOffer/JobSeeker DTOs. Implement bargaining via snapshots.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_labor_api_dto_SPEC.md"
    },
    "MISSION_test_stabilization": {
        "title": "Final Test Suite Stabilization (Post-Merge)",
        "instruction": "Run `pytest -rfE --tb=line --no-header tests/` and fix all remaining test failures (ImportErrors, DTO signature mismatches) incrementally until the suite passes 100%.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_test_stabilization_SPEC.md"
    }
}
