### 1. 🔍 Summary
M2 통화량 누수 버그(Ghost money)를 해결하기 위해 `CentralBankSystem`에 전역 트랜잭션 리스트를 주입하는 패턴을 도입하고, `MonetaryLedger`의 M2 집계 대상과 채권 상환 처리 로직을 수정했습니다.

### 2. 🚨 Critical Issues
- **[State Purity Violation] 전역 상태 직접 수정**: `simulation/systems/central_bank_system.py`의 `__init__`에서 `world_state.transactions`라는 전역 가변 리스트를 주입받아, `mint` 등의 내부 로직에서 직접 `self.transactions.append(tx)`를 호출하고 있습니다. 이는 "모든 상태 변경은 Agent 또는 Orchestrator 클래스 내에서만 일어나야 한다"는 아키텍처 원칙에 정면으로 위배됩니다. 트랜잭션은 전역 리스트에 직접 삽입(Side-effect)하지 말고, 호출 스택을 통해 반환(Bubble-up)하여 최상위 Orchestrator나 Agent가 추가하도록 리팩토링해야 합니다.
- **[Dependency Purity Violation] Agent 핸들 참조**: `CentralBankSystem`의 초기화 함수에서 `central_bank_agent` 객체 자체를 인자로 받고 멤버 변수로 저장하고 있습니다. Engine 및 System 객체는 독립적이어야 하며 Agent의 핸들(`self`)을 직접 소유해서는 안 됩니다.
- **[Float Incursion Risk] 금액의 Float 캐스팅**: `modules/government/components/monetary_ledger.py`에서 `amount = float(repayment_details["principal"])`를 사용하고 있습니다. `SettlementSystem`은 금액에 대해 엄격한 `int` 타입을 요구하므로 (`amount must be int, got float` 예외 존재), 이 부분은 시스템 다운(Crash) 또는 부동소수점 오차를 유발할 수 있습니다. `int()` 또는 `int(float())`로 안전하게 수정해야 합니다.

### 3. ⚠️ Logic & Spec Gaps
- **Mock Purity 위반**: `tests/unit/test_tax_collection.py`의 `MockSettlementSystem.transfer`가 `MagicMock` 객체를 그대로 반환하고 있습니다. 이 `MagicMock` 객체가 DTO 리스트(`transactions`)에 주입되어 반환되면, 실제 속성 기반의 검증 로직을 무력화시키고 의도치 않은 동작을 유발할 수 있습니다. 실제 `Transaction` 객체나 `dataclass` 기반의 원시 데이터를 반환하도록 수정하십시오.

### 4. 💡 Suggestions
- `WO-WAVE5-MONETARY-FIX.md` 인사이트 보고서가 `현상/원인/해결/교훈` 템플릿 구조를 따르지 않고 자유 형식으로 작성되어 있습니다. 표준 템플릿에 맞춰 일관성 있게 재작성할 것을 권장합니다.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**: "To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions to the global ledger."
- **Reviewer Evaluation**: 통화량 누수의 원인(LLR 과정에서의 보이지 않는 트랜잭션 발생)을 추적해 낸 분석의 기술적 깊이는 훌륭합니다. 하지만 이를 해결하기 위해 채택한 "Transaction Injection Pattern"은 심각한 안티 패턴입니다. 하위 시스템(System)이 전역 상태(WorldState의 List)를 주입받아 부수 효과(Side-effect)를 발생시키는 방식은 상태 관리의 순수성과 추적성을 파괴합니다. 이 인사이트는 해결책의 아키텍처적 결함을 인지하고, 트랜잭션을 상위 호출자로 반환(Bubble-up)하는 방향으로 수정 및 재평가되어야 합니다.

### 6. 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`
- **Draft Content**:
```markdown
### 2026-02-27: M2 통화량 누수 및 시스템 상태 순수성 위반 (WO-WAVE5-MONETARY-FIX)
- **현상**: M2 통화량이 실제 발행된 화폐량과 일치하지 않고 누수되는 현상 발생.
- **원인**: 중앙은행(Lender of Last Resort)이 시스템 깊은 곳에서 개입하여 화폐를 발행할 때, 생성된 트랜잭션이 전역 원장(WorldState.transactions)에 기록되지 않고 휘발됨. 또한 채권 상환 시 원금과 이자가 모두 M2 소각으로 처리됨.
- **해결**: `MonetaryLedger`의 M2 집계 대상을 명확히 하고 채권 상환 시 원금만 소각으로 처리하도록 수정. 단, 누락된 트랜잭션을 기록하기 위해 하위 시스템(`CentralBankSystem`)에 전역 상태 리스트를 주입하는 방식은 상태 순수성 원칙 위배로 반려됨.
- **교훈**: 하위 시스템(Engine/System)은 전역 상태를 주입받아 직접 조작해서는 안 되며, 발생한 트랜잭션이나 이벤트를 반환값(Bubble-up)으로 상위에 전달하여 Agent나 Orchestrator가 상태 변경을 통제하도록 설계해야 함. 또한 금액 연산 시 부동소수점(`float()`)의 유입은 시스템 전체의 정수형 통화 룰을 파괴하므로 철저히 차단해야 함.
```

### 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**