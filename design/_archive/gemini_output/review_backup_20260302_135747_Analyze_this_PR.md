# Code Review Report

## 🔍 Summary
이번 PR은 LLR 등의 암시적 통화 발행 과정에서 누락되던 트랜잭션을 전역 렛저에 주입(Injection)하여 M2 무결성을 개선하고, 채권 상환 시 원금과 이자를 분리하여 정확한 통화 소각을 추적하며, M2 계산에서 시스템 에이전트를 제외하도록 궤도를 수정했습니다.

## 🚨 Critical Issues
- **None Detected**: 명시적인 시스템 키/URL 하드코딩이나 제로섬 파괴 버그는 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps
- **SSoT & Dependency Purity Bypass (Vibe Check Fail)**: `simulation/systems/central_bank_system.py`에서 `WorldState.transactions` 리스트의 참조를 파라미터로 주입받아 내부에서 직접 `.append(tx)`를 호출해 전역 상태를 오염(Mutate)시키고 있습니다. 이는 컴포넌트가 상태를 직접 수정하지 않아야 한다는 무상태 엔진(Stateless Engine) 및 상태 위임 원칙을 완전히 우회하는 설계입니다. 
- **Float Incursion Risk**: `modules/government/components/monetary_ledger.py`에서 채권 원금 처리 시 `amount = float(repayment_details["principal"])`와 같이 의도적으로 `float` 캐스팅을 사용하고 있습니다. `SettlementSystem`이 `FloatIncursionError`를 발생시킬 정도로 정수형(Integer) 무결성을 강조하는 금융 시스템에서 `float` 사용은 부동소수점 오차 누적을 유발할 수 있습니다. `int()` 변환을 사용해야 합니다.
- **Hot Loop Performance Penalty**: `simulation/world_state.py`의 `calculate_total_money` 함수 루프 내에서 매 에이전트마다 `str(holder.id)` 변환과 `str(ID_CENTRAL_BANK)` 등의 비교를 반복하고 있습니다. 틱마다 전체 인구를 대상으로 실행되는 로직이므로 심각한 성능 오버헤드가 발생할 수 있습니다.

## 💡 Suggestions
- `CentralBankSystem`의 `mint()`와 `transfer_and_burn()` 메서드가 부수 효과(리스트 직접 수정)를 일으키는 대신, 생성된 `Transaction` 객체를 `Return`하게 하고, 이를 호출한 에이전트나 Orchestrator에서 `WorldState`에 반영하도록 구조를 리팩토링하십시오 (`Government.execute_social_policy`의 개선 사례를 동일하게 참고).
- `world_state.py`의 M2 계산 루프에 진입하기 전에 `system_sinks = {str(ID_CENTRAL_BANK), str(ID_PUBLIC_MANAGER), str(ID_SYSTEM)}` 형태의 캐싱된 Set을 선언하고 루프 내에서는 `str(holder.id) in system_sinks`로 O(1) 조회를 수행하도록 최적화하십시오.
- `monetary_ledger.py`의 채권 원금 캐스팅을 `int(repayment_details["principal"])` (혹은 프로젝트 표준 소수점 처리 방식)으로 수정하십시오.

## 🧠 Implementation Insight Evaluation
- **Original Insight**: 
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`. To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. This ensures that every penny created or destroyed is visible to the audit system, regardless of where in the call stack the operation occurred.
- **Reviewer Evaluation**: 통화량 측정(M2) 무결성의 누수 지점을 찾아내고 원인을 규명한 분석 자체는 매우 정확하고 훌륭합니다. 하지만 해결책으로 명명한 "Transaction Injection Pattern"은 하위 도메인 객체(`CentralBankSystem`)에게 전역 상태(글로벌 리스트)의 직접 변경 권한을 묵인하여 부여하는 명백한 안티패턴(State Mutation Leak)입니다. 단기적으로는 회계 무결성이 확보될지 모르나 장기적으로는 시스템의 의존성 순수성을 파괴하고 부수 효과 추적을 어렵게 합니다. 하위 시스템에서는 발생한 트랜잭션을 '반환(Return)'만 수행하고, 단일 통제점(Orchestrator)에서 이를 전역 렛저에 반영하도록 개선해야 합니다.

## 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
  ```markdown
  ### [Date] CentralBankSystem State Mutation Bypass (Transaction Injection)
  - **현상 (Symptom)**: `CentralBankSystem` 초기화 시 `WorldState.transactions` 참조를 주입받아, 내부 로직(Mint 등)에서 전역 상태인 트랜잭션 리스트를 직접 `.append()` 함.
  - **원인 (Cause)**: 깊은 콜스택 내부에서 발생하는 부수 효과(Mint/Burn 트랜잭션)를 상위로 반환(return)하여 릴레이하기 번거롭다는 이유로, 전역 상태 객체의 참조를 하위 모듈에 넘기는 우회(Bypass) 패턴을 선택함.
  - **해결/권장사항 (Resolution)**: `CentralBankSystem`의 전역 참조 주입 구조를 제거하고, 통화 조작 메서드들이 발생한 `Transaction` 객체를 반환(Return)하도록 리팩토링할 것. 상태의 변경 권한과 기록 처리는 제어 흐름의 최상단(Orchestrator 또는 시스템 Agent)에 위임하여야 함.
  - **교훈 (Lesson)**: 단기적인 버그 수정을 위해 하위 객체에 전역 상태 변경 권한을 부여하면 시스템의 의존성 순수성이 심각하게 훼손된다. "SSoT(Single Source of Truth)의 모든 상태 업데이트는 반드시 명시적 반환을 통해 중앙집중적으로 통제되어야 한다."
  ```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**