# WO-AUDIT-M2-TICK1-JUMP: Technical Report

## Executive Summary
Tick 1에서 발생하는 약 104M의 M2 점프(Double-Counting) 현상은 Genesis 시점(Tick 0)에 `Bootstrapper`에 의해 주입된 초기 자금이 **(1) Initializer에 의해 Baseline M2로 설정**됨과 동시에, **(2) Tick 1 시작 시 MonetaryLedger의 Transaction Observer에 의해 다시 Expansion으로 집계**되기 때문에 발생합니다. `Bootstrapper`가 생성한 `GENESIS_GRANT` 및 `BOOTSTRAP_INJECTION` 트랜잭션이 레벨 트리거 방식으로 재처리되는 것을 방지하기 위한 로직 부재가 근본 원인입니다.

## Detailed Analysis

### 1. M2 점프의 메커니즘 분석
- **Step 1 (Tick 0 Initialization)**: `initializer.py:L482-489`에서 `calculate_total_money()`를 호출하여 `Bootstrapper`가 주입한 모든 자산(가계 지원금 약 100M + 기업 지원금 등)을 합산하여 `baseline_money_supply`를 결정하고, 이를 `ledger.set_expected_m2()`로 설정합니다.
- **Step 2 (Transaction Persistence)**: `Bootstrapper`가 사용한 `create_and_transfer`는 `Transaction` 객체를 생성하여 `world_state.transactions`에 기록합니다. 이 트랜잭션들의 `buyer_id`는 `ID_CENTRAL_BANK`입니다.
- **Step 3 (Tick 1 Observer Trigger)**: Tick 1이 시작되면서 시뮬레이션 엔진은 `monetary_ledger.process_transactions()`를 호출합니다.
- **Step 4 (Double Counting)**: `modules/finance/kernel/ledger.py:L161-164`에서 `buyer_id`가 `ID_CENTRAL_BANK`인 트랜잭션을 감지하여 `is_expansion = True`로 판정하고, `L190`에서 `self.expected_m2_pennies += amount`를 실행합니다. 이미 Baseline에 포함된 금액이 "새로운 확장"으로 중복 더해지며 104M의 점프가 발생합니다.

### 2. Bootstrapper 기록 정합성 확인
- **상태**: ✅ 부분적 기록 (과잉 기록)
- **증거**: `simulation/systems/bootstrapper.py:L36-41`에서 `create_and_transfer`를 호출하여 M2 확장을 유발하는 트랜잭션을 정상적으로 생성합니다. 그러나 이 트랜잭션이 "초기화용(Genesis)"임을 명시하는 플래그가 `ledger.py`의 관찰 로직에서 필터링되지 않습니다.

### 3. Requirements Verification
- **Zero-Sum Integrity**: ⚠️ 위배 (통화량이 시스템 외부에서 유입된 것으로 오인되어 기대 통화량과 실제 통화량의 괴리 발생)
- **Logic Separation**: ❌ 위배 (초기화 로직과 런타임 통화 정책 관찰 로직이 충돌함)

## Risk Assessment
- **State Pollution**: `expected_m2_pennies`가 실제 유통 통화량의 2배로 팽창하여 금리 결정 및 인플레이션 추적기(`EconomicIndicatorTracker`)에 심각한 왜곡을 전달합니다.
- **Duct-Tape Risk**: 단순히 Tick 1에서 수치를 보정하는 방식은 차후 시나리오 재생(Replay) 시 불일치를 초래할 수 있는 고위험 요소입니다.

## Conclusion
Tick 1의 M2 점프는 시뮬레이션의 경제적 신뢰성을 무너뜨리는 중대한 결함입니다. Genesis 트랜잭션에 `is_genesis=True` 또는 `is_audit=True` 메타데이터를 강제하고, `MonetaryLedger`가 이를 감지하여 통화량 집계에서 제외하도록 수정해야 합니다.

---

# MISSION_WO-SPEC-M2-INTEGRITY_SPEC.md

## 1. 문제 정의
- **현상**: Tick 1 진입 시 M2(광의 통화) 수치가 초기 설정값 대비 약 104,000,000 penny(1.04M USD) 급증함.
- **원인**: `Bootstrapper`의 자금 주입 트랜잭션이 Tick 0의 Baseline에 포함된 후, Tick 1의 `process_transactions` 관찰 루프에서 신규 통화 팽창으로 중복 처리됨.

## 2. 해결 전략: Genesis Transaction Neutralization
`Bootstrapper`가 생성하는 모든 초기 자산 형성 트랜잭션에 감사용 플래그를 삽입하고, `MonetaryLedger`가 이를 무시하도록 변경합니다.

### 2.1. 수정 사항 A: `simulation/systems/bootstrapper.py`
- `distribute_initial_wealth` 및 `inject_liquidity_for_firm` 내 `create_and_transfer` 호출 시 `metadata`에 `{"is_genesis": True, "is_audit": True}`를 포함하도록 수정.
- **기대 효과**: 트랜잭션 로그에는 남되, 경제적 '변화'가 아닌 '상태'로 정의함.

### 2.2. 수정 사항 B: `modules/finance/kernel/ledger.py`
- `process_transactions` 메서드 내 상단에 메타데이터 체크 로직 추가.
```python
# modules/finance/kernel/ledger.py 예상 수정안
for tx in transactions:
    metadata = getattr(tx, 'metadata', {}) or {}
    if metadata.get('is_genesis') or metadata.get('is_audit'):
        continue # 초기화 자금은 중복 집계 방지를 위해 스킵
```
- **기대 효과**: Tick 1에서 Tick 0의 트랜잭션을 재처리할 때 통화량 변화(Delta)를 발생시키지 않음.

### 2.3. 수정 사항 C: `simulation/initialization/initializer.py`
- Phase 5의 `set_expected_m2` 호출 시점을 최적화하거나, 주입 직후 Ledger의 `reset_tick_flow()`를 호출하여 스냅샷 불일치 제거.

## 3. 검증 계획
1. `tests/test_money_supply_integrity.py`를 작성하여 Tick 0과 Tick 1의 `expected_m2_pennies` 차이가 0임을 검증.
2. `CentralBank`의 M0 발행량과 `MonetaryLedger`의 M2 합계가 일치하는지 확인.

---

# insight report: communications/insights/WO-AUDIT-M2-TICK1-JUMP.md

## 1. Architectural Insights
- **Initialization vs. Observation**: 시뮬레이션 시스템에서 "초기 상태 설정(Genesis)"과 "상태 변화 관찰(Observation)" 사이의 명확한 경계가 필요합니다. 현재 `MonetaryLedger`는 트랜잭션 로그를 기반으로 하는 관찰자(Observer) 패턴을 사용하는데, 초기화 과정에서 발생한 로그를 런타임 변화로 오인하는 'Bootstrapping Paradox'가 확인되었습니다.
- **Idempotency of Transactions**: 통화 시스템의 트랜잭션은 멱등성(Idempotency)을 가져야 하며, 특히 초기 자금 주입과 같은 특수 트랜잭션은 메타데이터를 통해 그 성격이 명시적으로 정의되어야 합니다.

## 2. Regression Analysis
- 본 분석은 코드 수정 제안 단계로, 기존 테스트를 파괴하지 않습니다. 오히려 `test_money_supply_dto.py` 등에서 발견되었을 수 있는 "기대값보다 높은 통화량" 문제를 해결하는 기반이 됩니다.
- 향후 수정 시 `MonetaryLedger`의 `process_transactions`가 모든 `ID_CENTRAL_BANK` 발신 트랜잭션을 무조건 팽창으로 보지 않도록 보완해야 하므로, 관련 단위 테스트의 업데이트가 필요할 수 있습니다.

## 3. Test Evidence
*이 보고서는 분석 보고서이며, 실제 코드 수정 및 pytest 실행 결과는 수정 작업 완료 후 제공될 예정입니다.*
*현재 상태에서의 진단 결과:*
- **Failing Scenario**: Tick 1 Start
- **Expected M2**: 104,000,000
- **Actual M2**: 208,000,000 (Calculated via logic trace)
- **Root Cause**: `MonetaryLedger.process_transactions` double-counts Tick 0 grants.