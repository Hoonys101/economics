**🔍 Summary**
이번 PR은 시스템 전반의 유동성 누수(M2 Leakage) 문제를 해결하기 위해 Central Bank의 묵시적 통화 발행을 전역 트랜잭션 큐에 강제 주입(Injection)하고, 채권 상환 시 원금과 이자를 분리하여 M2 감소량을 보다 정확히 산정하도록 개선했습니다. 그러나, Phase 1(`pr_diff.patch`)과 Phase 2(`pr_diff_phase2.txt`)의 변경 사항이 충돌하여 심각한 초기화 런타임 에러(TypeError)를 유발할 위험이 있습니다.

**🚨 Critical Issues**
1. **`Initializer` 로직 충돌 및 TypeError 위험 (Hard-Fail)**:
   - `pr_diff.patch`에서는 `CentralBankSystem`의 `__init__` 시그니처에 필수 위치 인자(Positional Argument)인 `transactions`가 추가되었습니다.
   - 하지만 `pr_diff_phase2.txt`의 `initializer.py` 변경 사항(Line 206 부근)을 보면, `CentralBankSystem` 생성 및 위치 이동을 수행하면서 `transactions` 인자가 누락된 채 과거 시그니처로 초기화(`sim.central_bank_system = CentralBankSystem(..., logger=self.logger)`)하고 있습니다.
   - 이 두 파일이 함께 머지되어 실행될 경우 시뮬레이션 초기화 단계에서 `TypeError: CentralBankSystem.__init__() missing 1 required positional argument: 'transactions'`가 발생하며 전체 시스템이 크래시(Crash)됩니다. 즉시 수정해야 합니다.

**⚠️ Logic & Spec Gaps**
1. **Duck-Typing을 통한 통화 권한 확인 지양**:
   - `FinanceSystem` (`pr_diff_phase2.txt`)에서 LLR 유동성 요청 시 `if hasattr(self.monetary_authority, 'check_and_provide_liquidity'):` 패턴을 사용하고 있습니다. 이는 프로젝트의 강타입(Strong Typing) 및 인터페이스 지향 설계 원칙에 어긋납니다. `IMonetaryAuthority` 또는 `ICentralBank` 프로토콜에 해당 메서드를 공식적으로 정의하여 하드코딩된 Duck-Typing을 피해야 합니다.
2. **잠재적 부동소수점 오차(Float Incursion)**:
   - `modules/government/components/monetary_ledger.py`에서 채권 원금 상환액을 파싱할 때 `amount = float(repayment_details["principal"])` 로 캐스팅하고 있습니다. 전체 시스템의 회계 단위가 페니(Integer)로 이주(Migration)한 상태이므로, 잠재적인 Float Incursion을 방지하기 위해 `int(...)` 또는 `Decimal(...)`로 안전하게 변환하는 것이 바람직합니다.
3. **Local Import 사용**:
   - `simulation/systems/central_bank_system.py`의 `check_and_provide_liquidity` 메서드 내부에 `from modules.system.api import DEFAULT_CURRENCY`가 하드코딩되어 있습니다. 이를 파일 상단의 `TYPE_CHECKING` 블록이나 모듈 레벨의 Import로 이동시켜 의존성을 깨끗하게 관리해야 합니다.

**💡 Suggestions**
1. **전역 큐 주입 패턴의 인터페이스화**:
   - `CentralBankSystem`에 `transactions: List[Any]`를 직접 주입하여 내부에서 `append` 하는 방식은 객체의 캡슐화를 약화시킬 수 있습니다. 향후 리팩토링 시, 리스트를 직접 받기보다 `ITransactionQueue` 프로토콜이나 Event Emitter 패턴을 도입하여 엔진들이 트랜잭션을 상위 계층으로 보다 안전하게 위임(Bubble-up)할 수 있도록 구조를 개선할 것을 제안합니다.

**🧠 Implementation Insight Evaluation**
- **Original Insight**: 
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`. To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`...
- **Reviewer Evaluation**: 
  - Jules가 작성한 원문 인사이트는 현상("ghost money" creation), 원인(implicit system operations bypassing global ledger), 그리고 해결책(Transaction Injection Pattern)을 매우 정확하게 파악하고 있습니다. 기술 부채의 본질을 완벽히 이해한 훌륭한 진단입니다.
  - 다만, 훌륭한 인사이트와는 별개로 앞서 언급한 `initializer.py`에서의 초기화 시그니처 덮어쓰기 문제로 인해 해당 해결책이 실행조차 되지 못하는 상태가 되었습니다. 기술적 교훈의 가치를 실현하려면 코드 병합(Merge) 시 충돌 관리에 더욱 주의해야 합니다.

**📚 Manual Update Proposal (Draft)**
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
```markdown
### [WO-WAVE5-MONETARY-FIX] Ghost Money & System Sink Auditing
- **Date**: 2026-02-28
- **Problem**: 시뮬레이션 중 M2(통화 공급량)가 예상치와 심각하게 틀어지거나 누수(Leakage)되는 현상이 발생. 중앙은행의 LLR(Lender of Last Resort) 기능 등 묵시적 시스템 운영 과정에서 생성된 화폐가 전역 `WorldState` 트랜잭션 큐에 기록되지 않아, 회계 시스템에 잡히지 않는 "Ghost Money"가 발생하는 것이 원인으로 확인됨.
- **Solution**: 
  1. `CentralBankSystem`에 전역 Transaction 큐를 의존성으로 주입(Injection)하여, 묵시적 발행(Mint)이나 소각(Burn) 트랜잭션이 발생할 경우 즉시 원장으로 버블링되도록 구조를 변경.
  2. M2의 정의(Perimeter)를 보수적으로 재조정하여 `ID_PUBLIC_MANAGER`와 `ID_SYSTEM` 같은 시스템 잉여 계정을 Central Bank와 함께 System Sinks로 분류, 불필요한 유동성 변동 착시를 제거.
- **Lesson Learned**: 시스템 에이전트(Central Bank, Settlement 등)의 자동화된 동작(State 변경)이라 하더라도, 반드시 원장에 기록되는 **명시적 트랜잭션(Explicit Transaction)** 형태를 띄고 중앙 큐를 거쳐야만 Double-Entry 및 M2 무결성 검증을 통과할 수 있다.
```

**✅ Verdict**
**REQUEST CHANGES (Hard-Fail)**