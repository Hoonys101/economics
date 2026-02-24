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
    "WO-WAVE6-CONTEXT-INJECTOR": {
        "title": "Wave 6-1: ContextInjectorService Restoration (Lazy Import)",
        "instruction": "dispatchers.py에서 ContextInjectorService의 commented-out 블록을 복구하십시오.\n\n⚠️ 핵심 제약: 순환 참조 방지를 위해 모든 import는 반드시 execute() 메서드 내부에서 lazy하게 수행해야 합니다.\n\n1. **GeminiDispatcher.execute()**: 메서드 본문 내에서 `from _internal.scripts.core.context_injector.service import ContextInjectorService`를 import하고, 기존 주석 처리된 context injection 로직을 복구하십시오.\n2. **JulesDispatcher.execute()**: 동일한 패턴으로 lazy import 및 context injection 로직을 복구하십시오.\n3. **검증**: `python -c \"from _internal.registry.commands.dispatchers import GeminiDispatcher, JulesDispatcher; print('OK')\"` 실행하여 import 에러가 없음을 확인하십시오.\n4. **테스트**: `pytest tests/ -k dispatcher` 실행하여 관련 테스트 통과를 확인하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_wave6_restoration_SPEC.md"
    },
    "WO-WAVE6-TRANSFER-HANDLER": {
        "title": "Wave 6-2: DefaultTransferHandler Implementation (TD-SYS-TRANSFER-HANDLER-GAP)",
        "instruction": "SettlementSystem이 생성하는 'transfer' 타입 트랜잭션을 위한 핸들러를 구현하십시오.\n\n⚠️ 핵심 제약: DefaultTransferHandler는 절대로 SettlementSystem.transfer()를 호출해서는 안 됩니다. SettlementSystem이 이미 자금 이동을 완료한 후 트랜잭션 레코드를 생성하므로, 핸들러는 MonetaryLedger 추적을 위한 pass-through 역할만 합니다.\n\n1. **신규 파일**: `simulation/systems/handlers/transfer_handler.py`에 `DefaultTransferHandler` 클래스를 생성하십시오. `ITransactionHandler`를 구현하며, `handle()` 메서드는 단순히 `True`를 반환합니다.\n2. **등록**: `simulation/initialization/initializer.py`에서 `DefaultTransferHandler`를 `'transfer'` 타입으로 `transaction_processor.register_handler()`에 등록하십시오.\n3. **검증**: `python scripts/operation_forensics.py --ticks 10` 실행 후 로그에서 'No handler for tx type: transfer' 경고가 사라졌는지 확인하십시오.\n4. **테스트**: `pytest tests/ -k transaction` 관련 테스트 통과를 확인하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_wave6_restoration_SPEC.md"
    },
    "WO-WAVE6-SSOT-ENFORCEMENT": {
        "title": "Wave 6-3: Penny Standard SSoT Enforcement (Settlement + Labor)",
        "instruction": "Transaction 레코드의 단위 정합성(Penny Standard)을 강제하십시오.\n\n1. **SettlementSystem 수정**: `settlement_system.py`의 `_create_transaction_record()`에서 Transaction 생성 시:\n   - `quantity`를 `1.0`으로 변경 (현재 `amount` 즉 페니 값이 들어가 있음)\n   - `price`를 `amount / 100.0`으로 변경 (달러 단위 표시가격)\n   - `total_pennies`는 그대로 `amount` 유지 (SSoT)\n\n2. **LaborTransactionHandler 감사**: `labor_handler.py`에서 `TaxationSystem.calculate_tax_intents()`에 전달되는 값이 `tx.total_pennies`(SSoT)를 기반으로 하는지 확인하십시오. 만약 TaxationSystem이 `tx.price * tx.quantity`를 사용한다면, `tx.total_pennies`를 사용하도록 수정하십시오.\n\n3. **Mock 업데이트**: Transaction을 Mock하는 모든 테스트에서 `total_pennies`가 명시적으로 설정되어 있는지 전수조사하십시오. 누락된 경우 추가하십시오.\n\n4. **검증**: `pytest tests/` 전체 실행하여 100% 통과를 확인하십시오. 보고서에 pytest 전체 출력을 포함하십시오.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_wave6_restoration_SPEC.md"
    },
    "WO-LIQUID-W1-STARTUP": {
        "title": "Phase 22 [W1]: Startup Foundation & FirmFactory",
        "instruction": "MISSION_grand_liquidation_SPEC.md의 Wave 1 항목 중 초기화 및 생성 로직을 해결하십시오.\n\n1. **TD-FIN-INVISIBLE-HAND (Init Order)**: `initializer.py`에서 `AgentRegistry` 스냅샷 이전에 `CentralBank`, `PublicManager`, `Government` 등 시스템 에이전트가 완전히 등록되도록 `build_simulation` 시퀀스를 조정하십시오.\n2. **TD-LIFECYCLE-GHOST-FIRM (FirmFactory)**: `FirmFactory` 클래스를 도입(또는 `Firm` 모듈 내 구현)하여 [생성 -> 계좌 개설 -> 유동성 주입]이 원자적으로 수행되도록 `initializer.py`의 `_setup_starting_firms`를 리팩토링하십시오.\n3. **TD-LIFECYCLE-NAMING**: `capital_stock_pennies`와 같이 단위가 모호한 변수들을 `capital_stock_pennies` (명시적) 또는 DTO를 통한 타입 안정성 확보로 정리하십시오.\n\n검증: `pytest tests/unit/lifecycle/` 및 `tests/system/test_engine.py` 통과 확인.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_grand_liquidation_SPEC.md"
    },
    "WO-LIQUID-W1-GOV-FIX": {
        "title": "Phase 22 [W1]: Gov Singleton & Orchestrator Hardening",
        "instruction": "MISSION_grand_liquidation_SPEC.md의 Wave 1 항목 중 아키텍처 불일치를 해결하십시오.\n\n1. **TD-ARCH-GOV-MISMATCH (Gov Singleton)**: `WorldState`에서 `governments` 리스트를 제거하고 단일 `government` 속성으로 통합하십시오. 모든 참조(Analytics, Taxation 등)를 이 단일 속성으로 전환하십시오.\n2. **TD-ARCH-ORCH-HARD (Orchestrator Hardening)**: `TickOrchestrator`에서 Mock 객체 사용 시 속성 누락으로 인한 에러를 방지하기 위해 `getattr(obj, 'attr', default)` 패턴 또는 명시적 프로토콜 체크를 강화하십시오.\n\n검증: `pytest tests/unit/systems/` 및 `tests/unit/test_analytics.py` 등 관련 테스트 통과 확인.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_grand_liquidation_SPEC.md"
    },
    "WO-LIQUID-W2-FINANCE": {
        "title": "Phase 22 [W2]: Financial Integrity & Saga Recovery",
        "instruction": "MISSION_grand_liquidation_SPEC.md의 Wave 2 금융/회계 항목을 해결하십시오.\n\n1. **TD-ECON-M2-REGRESSION (M2 Calculation)**: `calculate_total_money()`에서 음수 잔액을 합산하지 않고 `SystemDebt`로 분리하십시오.\n2. **TD-FIN-SAGA-REGRESSION (Saga Cleanup)**: `SagaOrchestrator`에 자동 정리 로직을 추가하여 죽은 에이전트 참조로 인한 `SAGA_SKIP` 스팸을 방지하십시오.\n3. **TD-INT-BANK-ROLLBACK (Strict Protocols)**: `hasattr` 체크 대신 `isinstance(agent, ITransactionRollback)` 프로토콜 체크를 적용하십시오.\n4. **TD-MARKET-FLOAT-TRUNC (Match Rounding)**: `MatchingEngine` 내 `int()` 절삭을 `round_to_pennies()`로 교체하십시오.\n\n검증: `pytest tests/unit/systems/` 및 `tests/unit/finance/` 통과 확인.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_grand_liquidation_SPEC.md"
    },
    "WO-LIQUID-W3-EVOLUTION": {
        "title": "Phase 22 [W3]: Domain Evolution & Test Hardening",
        "instruction": "MISSION_grand_liquidation_SPEC.md의 Wave 3 항목을 해결하십시오.\n\n1. **TD-WAVE3-DTO-SWAP (IndustryDomain Enum)**: 모든 DTO/Model에서 `major` 문자열을 `IndustryDomain` Enum으로 전면 교체하십시오.\n2. **TD-ECON-ZOMBIE-FIRM (Balance Tuning)**: `economy_params.yaml`의 필수재(basic_food) 관련 파라미터를 조정하여 초기 고사 현상을 방지하십시오.\n3. **TD-TEST-TX-MOCK-LAG (Test Debt)**: 레거시 Tax API 및 Mock 불일치를 전수 조사하여 수정하십시오.\n\n검증: `pytest tests/` 전체 통과 확인.",
        "file": "c:/coding/economics/gemini-output/spec/MISSION_grand_liquidation_SPEC.md"
    }
}
