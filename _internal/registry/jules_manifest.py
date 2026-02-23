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
    "MISSION_liquidation_wave1_shared_kernel": {
        "title": "Wave 1: Shared Financial Kernel & Cycle Breaker",
        "instruction": "Implement modules/common/financial, migrate Claim/MoneyDTO (Int Pennies), and resolve Finance <-> HR circular dependency as per SPEC.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_liquidation_wave1_SPEC.md"
    },
    "MISSION_liquidation_wave1_5_stability": {
        "title": "Wave 1.5: Initialization & Concurrency Stabilizer",
        "instruction": "Fix SimulationInitializer order, register Agent 0, and implement cross-platform file locking as per Wave 1.5 SPEC.",
        "file": "gemini-output/spec/MISSION_liquidation_wave1_5_SPEC.md"
    },
    # Add missions here
}
