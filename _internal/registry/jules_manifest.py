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
    "phase41_labor_implementation": {
        "title": "Implementation: Labor Market Major-Matching",
        "command": "create",
        "instruction": "Implement the Major-Matching logic in HREngine, Household, and LaborMarket as per MISSION_phase41_labor_design_SPEC.md. Use CanonicalOrderDTO.metadata['major'] for compatibility.",
        "file": "gemini-output/spec/MISSION_phase41_labor_design_SPEC.md"
    },
    "phase41_fx_barter_implementation": {
        "title": "Implementation: Multi-Currency Barter-FX",
        "command": "create",
        "instruction": "Implement atomic 'Penny-level Barter Swaps' in SettlementSystem. Ensure zero-sum integrity and floor-rounding for dust management as per MISSION_phase41_fx_barter_SPEC.md.",
        "file": "gemini-output/spec/MISSION_phase41_fx_barter_SPEC.md"
    },
    "phase41_firm_seo_implementation": {
        "title": "Implementation: Firm SEO Brain-Scan Readiness",
        "command": "create",
        "instruction": "Refactor all Firm Engines to ensure they are pure functions (stateless). Update the Firm orchestrator to handle record_expense and finalize_firing locally. Verify with Brain Scan simulations as per MISSION_phase41_seo_brain_scan_SPEC.md.",
        "file": "gemini-output/spec/MISSION_phase41_seo_brain_scan_SPEC.md"
    }
}
