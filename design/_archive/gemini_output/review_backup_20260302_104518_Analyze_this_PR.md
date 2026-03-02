### 🔍 Summary
CentralBankSystem의 암묵적 통화 발행(LLR) 및 소각 내역을 전역 트랜잭션 큐에 직접 주입(Transaction Injection)하도록 개선하여 M2 누락을 방지하고, Orchestrator의 중복 트랜잭션 처리 단계를 통합했습니다. M2 집계 시 관리형 시스템 에이전트(Public Manager, System 등)를 배제하고, 채권 상환 처리 시 이자를 제외한 '원금'만을 통화 수축으로 인식하도록 Ledger 정합성을 개선했습니다.

### 🚨 Critical Issues
- **Float Incursion in `MonetaryLedger`**: 
  - `modules/government/components/monetary_ledger.py` 파일의 85번째 라인 근처, `amount = float(repayment_details["principal"])`에서 심각한 무결성 위반이 발생했습니다.
  - 시스템은 페니(pennies) 단위의 정수(int) 기반 금융 무결성을 엄격하게 요구하며, `SettlementSystem`에서도 명시적으로 부동소수점 유입을 방지(`FloatIncursionError`)하고 있습니다.
  - `float` 캐스팅은 부동소수점 오차를 유발하고 `expected_m2_pennies`의 정수형 타입을 오염시키므로, 반드시 정수형으로 캐스팅(`int(repayment_details["principal"])`)해야 합니다.

### ⚠️ Logic & Spec Gaps
- **Side-Effect via Mutable List Injection**: 
  - `CentralBankSystem`에 `sim.world_state.transactions` 리스트의 참조를 직접 전달하여 내부에서 `.append(tx)`를 수행하는 방식은 객체 지향 및 함수형 캡슐화를 우회하는 암묵적인 상태 변경(Side-effect)입니다.
  - 현재 시스템 구조상 즉각적인 LLR의 작동 처리를 위해 불가피한 선택일 수 있으나, 가급적 시스템이나 엔진 계층에서는 발생한 트랜잭션을 반환(Return)하고, Orchestrator가 이를 취합하여 상태를 업데이트하는 순수(Stateless) 접근이 아키텍처 설계 원칙(SSoT 유지)에 더 부합합니다. (단기적 허용, 장기적 리팩토링 필요)

### 💡 Suggestions
- `WorldState.calculate_total_money`에서 매번 에이전트 순회 시마다 `str(holder.id)` 변환을 수행하는 것은 시뮬레이션 틱이 증가할수록 성능 저하를 유발할 수 있습니다. 상위 레벨(클래스 또는 모듈)에서 제외할 ID 집합을 Set 자료형으로 미리 캐싱(`EXCLUDED_M2_IDS = {str(ID_CENTRAL_BANK), str(ID_PUBLIC_MANAGER), str(ID_SYSTEM)}`)하고 `in` 연산자로 검사하는 것이 더 효율적입니다.

### 🧠 Implementation Insight Evaluation
- **Original Insight**:
  > **1. Ledger Synchronization via Transaction Injection**
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`.
  > To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`...
- **Reviewer Evaluation**: 
  - M2 "Ghost Money" 현상의 근본 원인을 SettlementSystem의 반환값(tx) 누락으로 정확하게 진단하고 분석한 점은 훌륭합니다. 
  - 그러나 해결책으로 제시된 'Transaction Injection Pattern'에 대한 기술적 부채 평가는 부족합니다. 전역 상태(`transactions` 리스트)의 참조를 하위 시스템 객체에 하드와이어링(Hard-wiring)하는 것은 안티패턴에 가깝습니다. 통찰의 문제 해결 방향성은 타당하나, 아키텍처 순수성(Stateless) 측면에서 추후 EventBus 패턴이나 명시적 Event Return 방식으로 개선이 필요하다는 자기 성찰적 교훈이 보강되어야 완벽한 인사이트가 될 것입니다.

### 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
```markdown
### [WO-WAVE5-MONETARY-FIX] Implicit Transaction Leakage & State Mutation
- **현상 (Symptom)**: CentralBankSystem의 LLR(Lender of Last Resort) 개입 등 암묵적 통화 발행 시, 생성된 트랜잭션이 전역 `WorldState.transactions`에 기록되지 않아 M2 Ledger 집계에서 누락되는 현상(Ghost Money) 발생.
- **원인 (Cause)**: SettlementSystem이 개별 시스템 내부에서 호출될 때, 생성된 Transaction 객체가 상위 Orchestrator 레벨로 버블링(Return)되지 않고 소멸됨.
- **해결 (Resolution)**: `CentralBankSystem` 초기화 시 전역 트랜잭션 큐(`transactions` 리스트)의 참조를 주입하여, 처리 결과 트랜잭션을 직접 `.append()` 하도록 조치함.
- **교훈 및 기술 부채 (Lesson & Tech Debt)**: 가변 리스트(Mutable List)의 참조를 하위 시스템에 주입하여 전역 상태를 직접 변경하는 것은 Side-effect를 유발하며 Stateless 엔진 설계 원칙에 일부 위배됨. 향후 EventBus 패턴이나 명시적 Event/Transaction Return 방식으로 리팩토링하여 시스템 객체의 부수 효과(Side-effect)를 제거할 필요가 있음. 또한, 금액 처리 시 `float()` 캐스팅을 지양하고 항상 `int()`(pennies) 형식을 준수하여 잠재적인 Float Incursion을 선제적으로 차단해야 함.
```

### ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**
- **사유**: `MonetaryLedger`의 부동소수점(`float`) 캐스팅에 의한 명백한 `FloatIncursion` 보안/정합성 위반. 금융 시스템의 핵심 무결성 제약 조건인 정수(pennies) 사용 정책을 위반하므로 `int()` 형으로의 즉각적인 수정이 요구됩니다.