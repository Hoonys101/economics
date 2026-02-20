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
    "wave1-finance-protocol": {
        "title": "Wave 1.1: Financial Protocol Enforcement",
        "command": "create",
        "instruction": "Implement MISSION_wave1_finance_protocol_spec.md. Ensure IInvestor and IPropertyOwner protocols are used in MonetaryTransactionHandler, fix accounting for buyer expenses, and enforce strict rollback in the Bank interface.",
        "file": "artifacts/specs/MISSION_wave1_finance_protocol_spec.md"
    },
    "wave1-lifecycle-hygiene": {
        "title": "Wave 1.2: System Lifecycle & Dependency Hygiene",
        "command": "create",
        "instruction": "Implement MISSION_wave1_lifecycle_hygiene_spec.md. Create SystemFactory for SettlementSystem DI, optimize DeathSystem agent removal, and scrub inter_tick_queue upon agent death.",
        "file": "artifacts/specs/MISSION_wave1_lifecycle_hygiene_spec.md"
    },
    "wave2-firm-architecture": {
        "title": "Wave 2.1: Firm Architecture Overhaul",
        "command": "create",
        "instruction": "Implement MISSION_wave2_firm_architecture_spec.md. Remove self.parent from Firm departments, enforce DTO passing, and ensure Brand/Sales/HR Engines return ResultDTOs without mutating state.",
        "file": "artifacts/specs/MISSION_wave2_firm_architecture_spec.md"
    },
    "wave2-market-policy": {
        "title": "Wave 2.2: Market & Policy Refinement",
        "command": "create",
        "instruction": "Implement MISSION_wave2_market_policy_spec.md. Introduce CanonicalOrderDTO, implement StockIDHelper for robust ID parsing, and add TaxBracketDTO for progressive taxation in the Government.",
        "file": "artifacts/specs/MISSION_wave2_market_policy_spec.md"
    },
    "wave3-analytics-purity": {
        "title": "Wave 3.1: Operational & Analytics Purity",
        "command": "create",
        "instruction": "Implement MISSION_wave3_analytics_purity_spec.md. Refactor AnalyticsSystem to use SnapshotDTOs instead of direct agent references, and enforce Pydantic models for UI telemetry.",
        "file": "artifacts/specs/MISSION_wave3_analytics_purity_spec.md"
    },
    "wave3-dx-config": {
        "title": "Wave 3.2: Developer Experience & Config Hardening",
        "command": "create",
        "instruction": "Implement MISSION_wave3_dx_config_spec.md. Create a ConfigProxy for dynamic configuration resolution and set up an auto-discovery mechanism for Gemini manifest registration.",
        "file": "artifacts/specs/MISSION_wave3_dx_config_spec.md"
    }
}
