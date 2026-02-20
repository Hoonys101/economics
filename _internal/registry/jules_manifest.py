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
    "firm-ai-hardening": {
        "title": "Firm Refactor & AI Debt Awareness Hardening",
        "command": "create",
        "instruction": "Implement the changes specified in the MISSION_spec to decouple Firm components and harden AI debt awareness.",
        "file": "artifacts/specs/MISSION_firm_ai_hardening_spec.md"
    },
    "market-systems-hardening": {
        "title": "Market Precision & Robustness Hardening",
        "command": "create",
        "instruction": "Implement the MISSION_spec to fix unsafe quantization and robustify firm_id parsing.",
        "file": "artifacts/specs/MISSION_market_systems_hardening_spec.md"
    },
    "finance-purity-refactor": {
        "title": "Finance Protocol Purity Refactor",
        "command": "create",
        "instruction": "Implement the MISSION_spec to refactor MonetaryTransactionHandler to use strict Protocols.",
        "file": "artifacts/specs/MISSION_finance_purity_refactor_spec.md"
    },
    "firm-decoupling": {
        "title": "Firm Architecture Decoupling (Constants & Protocols)",
        "command": "create",
        "instruction": "Implement the MISSION_spec to decouple Firm from concrete LoanMarket using ILoanMarket Protocol and move FinanceEngine constants to FinanceConfigDTO.",
        "file": "artifacts/specs/MISSION_firm_decoupling_spec.md"
    }
}
