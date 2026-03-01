**🔍 Summary**
이 PR은 `CentralBankSystem`에 전역 Transaction 리스트를 주입(Transaction Injection)하여 암묵적으로 발행되던 LLR(Lender of Last Resort) 개입 자금 등의 Ghost Money를 추적 가능하게 수정하고, M2 집계 시 시스템 기관들의 소유분을 제외하여 정합성을 교정했습니다. 또한 본드 상환 시 원금만 M0/M2에서 차감되도록 원장(Ledger) 처리 로직을 개선했습니다. 

**🚨 Critical Issues**
- **[테스트 및 위생] Mock Purity Violation**: 
  - `tests/unit/test_tax_collection.py`의 `MockSettlementSystem`에서 `tx = MagicMock()` 객체를 반환하고 있습니다. `TESTING_STABILITY.md` 규칙에 따라 DTO나 핵심 모델의 반환 값으로 원시 `MagicMock`을 직접 사용하는 것은 금지되어 있습니다. `namedtuple`이나 최소한의 필드를 갖춘 데이터 클래스(또는 `MockTransaction` 클래스)로 대체해야 합니다.
- **[설정 및 의존성 순수성] Duck-typing & Type Safety Violation**: 
  - `modules/finance/system.py`의 `FinanceSystem.__init__`에서 `monetary_authority`의 타입이 `Optional[Any]`로 지정되어 있으며, `issue_bonds` 메서드 내부에서 `hasattr(self.monetary_authority, 'check_and_provide_liquidity')`를 호출하여 기능 존재 여부를 동적으로 검사하고 있습니다. 이는 명시적 인터페이스(Protocol) 기반 설계를 위반합니다. `ILenderOfLastResort` 혹은 관련 인터페이스를 정의하고, 타입을 명확히 지정하여 `hasattr` 검사를 제거해야 합니다.

**⚠️ Logic & Spec Gaps**
- **Global State Mutation (Side Effect)**: `simulation/systems/central_bank_system.py`에서 시스템 초기화 시 `WorldState.transactions` 리스트 자체를 참조로 넘겨받아(`self.transactions = transactions`), 깊은 계층에서 `self.transactions.append(tx)`로 전역 상태를 직접 변이(Mutation)시키고 있습니다. 이는 단기적으로 문제를 해결하지만, `TickOrchestrator`의 Phase 원자성과 생명주기 제어권을 약화시킵니다.
- **Inline Import**: `simulation/systems/central_bank_system.py`의 `check_and_provide_liquidity` 메서드 내부에서 `from modules.system.api import DEFAULT_CURRENCY` 지연 임포트가 발생하고 있습니다. 이는 런타임 성능 저하 및 모듈 참조 구조상 불안정성을 야기할 수 있으므로, 상단 임포트(필요시 `TYPE_CHECKING` 활용)로 수정하거나 매개변수로 받아야 합니다.

**💡 Suggestions**
1. `CentralBankSystem`이 `transactions` 리스트를 직접 수정하지 않도록, `check_and_provide_liquidity`나 `mint_and_transfer`가 `Transaction` (또는 `Optional[Transaction]`)을 반환하게 하고 상위 호출자(예: FinanceSystem이나 Orchestrator)가 이를 취합하여 상태에 커밋하는 방식(Return-based Aggregation)으로 리팩토링할 것을 권장합니다.
2. `FinanceSystem` 주입을 위해 `modules/finance/api.py` (혹은 적절한 API 정의 위치)에 `check_and_provide_liquidity`를 포함하는 명확한 `Protocol`을 정의하십시오.

**🧠 Implementation Insight Evaluation**
- **Original Insight**: 
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections... To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. This ensures that every penny created or destroyed is visible to the audit system...
- **Reviewer Evaluation**: 
  통화 누수(Ghost Money)의 원인을 LLR과 SettlementSystem 간의 사각지대에서 정확히 짚어냈으며, M2와 본드 상환 시 원금과 이자를 분리하여 계상하는 로직 역시 회계적(Accounting)으로 매우 타당합니다. 하지만, 채택된 **Transaction Injection Pattern**은 하위 시스템이 전역 트랜잭션 큐를 직접 변이(mutate)시키는 Anti-Pattern을 낳았습니다. 단기적 무결성 확보에는 훌륭하지만 구조적인 결합도를 높였으므로 기술 부채로 기록할 가치가 높습니다. 인사이트 보고서 누락 없이 잘 작성되었습니다.

**📚 Manual Update Proposal (Draft)**

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
**Draft Content**:
```markdown
### [WO-WAVE5-MONETARY-FIX] System Agent Transaction Bubbling
- **현상**: Central Bank의 LLR(Lender of Last Resort) 개입 등 시스템 내부에서 발생하는 암묵적 자금 발행이 글로벌 트랜잭션 큐(`WorldState.transactions`)에 기록되지 않아, M2 Audit 시 자금 누수 및 Ghost Money가 발생함.
- **원인**: `SettlementSystem` 내부에서 발생하는 시스템 간 자금 이동이 Orchestrator가 관리하는 트랜잭션 생명주기 외부에서 발생하기 때문.
- **해결**: `CentralBankSystem`에 `WorldState.transactions` 리스트를 참조로 주입(Transaction Injection)하여 시스템 주체가 직접 전역 큐에 트랜잭션을 Append 하도록 수정하여 가시성을 확보함.
- **교훈 및 기술 부채**: 하위 시스템이 상위 Orchestrator의 전역 상태(List)를 직접 변이(Mutate)시키는 방식은 Side Effect를 발생시킬 수 있습니다. 향후, 이들 시스템 오퍼레이션이 트랜잭션 객체를 직접 '반환(Return)'하고 이를 Orchestrator Phase에서 취합하여 일괄 반영하는 구조(Return-based Aggregation)로 리팩토링할 필요가 있습니다.
```

**✅ Verdict**
**REQUEST CHANGES (Hard-Fail)**
보안 위반은 없으나, 테스트 코드 내 `MagicMock` 직접 반환(Mock Purity 위반)과 `FinanceSystem`의 의존성 역전 및 타입 안정성 우회(`Any`, `hasattr` 사용) 이슈를 수정해야 합니다. 인사이트 보고서는 훌륭하게 작성되었습니다. 수정 후 재리뷰를 요청해 주십시오.