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
    "phase41_bank_registry_impl": {
        "title": "Implement BankRegistry Service Extraction",
        "file": "gemini-output/spec/MISSION_bank_registry_FREEZE.md",
        "instruction": "Extract bank account indexing from SettlementSystem into BankRegistry. Refactor SettlementSystem to use IBankRegistry. Update tests.",
        "wait": False
    },
    "phase41_labor_config_impl": {
        "title": "Implement Labor Config Externalization",
        "file": "gemini-output/spec/MISSION_labor_config_FREEZE.md",
        "instruction": "Externalize labor majors to economy_params.yaml. Update constants.py and LaborMarket.configure. Ensure backward compatibility.",
        "wait": False
    },
    "phase41_labor_metadata_impl": {
        "title": "Implement Labor Metadata DTO Migration",
        "file": "gemini-output/spec/MISSION_labor_metadata_SPEC.md",
        "instruction": "Migrate LaborMarket to use LaborMatchDTO instead of raw Order.metadata. Update Firm and Household call sites.",
        "wait": False
    },
    "phase41_test_dto_hygiene_impl": {
        "title": "Implement DTO Test Hygiene",
        "file": "gemini-output/spec/MISSION_test_dto_hygiene_SPEC.md",
        "instruction": "Create FirmFactory in tests/factories/ and refactor test_firm_brain_scan.py to eliminate permissive MagicMocks for DTOs.",
        "wait": False
    }
}
