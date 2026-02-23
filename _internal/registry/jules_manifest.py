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
    "MISSION_fix_wave5_regressions": {
        "title": "Wave 5: Critical Regressions Fix (Firm AI & Politics Orchestrator)",
        "instruction": "Wave 5 머지 후 발생한 2가지 핵심 에러를 수정하십시오.\n\n1. **`firm_ai.py` (calculate_reward)**: `current_assets`와 `prev_assets`가 `MultiCurrencyWalletDTO`인 경우를 처리하지 못해 `TypeError`가 발생합니다. `isinstance(raw, MultiCurrencyWalletDTO)` 체크를 추가하여 `.balances.get(DEFAULT_CURRENCY, 0)`을 안전하게 추출하십시오.\n2. **`orchestrator.py` (calculate_political_climate)**: 시스템 테스트(`TestPhase29Depression`)에서 Mock 에이전트를 사용할 때 `total_weight`가 `MagicMock`이 되어 `total_weight > 0` 비교 시 에러가 발생합니다. `weight` 추출 시 Mock 여부를 확인하거나, `total_weight` 연산 시 `float(weight)` 변환 등을 통해 방어 로직을 추가하십시오.\n3. **`test_phase29_depression.py`**: 가계 Mock 생성부에서 `political_weight` 등을 기본값(1.0)으로 설정하도록 업데이트하여 근본적인 Mock 불일치를 해결하십시오.\n\n수정 후 `pytest tests/system/test_phase29_depression.py` 및 `python scripts/operation_forensics.py`를 실행하여 무결성을 검증하십시오.",
    },
    "MISSION_wave5_runtime_stabilization": {
        "title": "Wave 5: Runtime Stabilization & Error Reduction Phase 3",
        "instruction": "MISSION_wave5_runtime_stabilization_SPEC.md를 바탕으로 런타임 오류를 50건 미만으로 줄이십시오. 통화량 동기화 및 비활성 에이전트 처리가 핵심입니다.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_wave5_runtime_stabilization_SPEC.md"
    },
    "WO-WAVE5-MONETARY-FIX": {
        "title": "Wave 5: Final Monetary Integrity & Audit Restoration",
        "instruction": "MISSION_wave5_monetary_audit_SPEC.md의 분석 결과를 바탕으로 화폐 정합성(Accounting Integrity)을 복구하십시오.\n\n1. **Ghost Money 해결**: `central_bank_system.py`에서 OMO/LLR 등으로 발생하는 M0 발행/소각 트랜잭션을 명시적으로 `world_state.transactions`에 큐잉하여 `MonetaryLedger`가 이를 감지할 수 있게 하십시오.\n2. **ID Type Mismatch 해결**: `world_state.py`의 `calculate_total_money`에서 ID 비교 시 `str()`을 사용하여 정수/문자열 불일치로 인한 합산 누락을 방지하십시오.\n3. **M2 Perimeter 일치**: M2 합산 시 `ID_PUBLIC_MANAGER(4)`와 `ID_SYSTEM(5)`를 제외하여 `MonetaryLedger`의 시스템 에이전트 정의와 동기화하십시오.\n4. **중복 계산 제거**: `TickOrchestrator`에서 `Phase_MonetaryProcessing`을 제거하고, `Phase3_Transaction`에 통합된 로직만 사용하도록 정리하십시오.\n5. **Forensics 검증**: 수정 후 `python scripts/operation_forensics.py`를 실행하여 Tick 1의 102M 점프와 2.6B 누출이 0으로 수렴하는지 확인하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_wave5_monetary_audit_SPEC.md"
    },
    # Add missions here
}
