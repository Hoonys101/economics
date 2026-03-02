# 🐙 Gemini CLI System Prompt: Git Reviewer Code Review Report

## 1. 🔍 Summary
Tick 1의 M2 점프 및 유령 화폐 문제를 해결하기 위해 CentralBankSystem에 Transaction Injection Pattern을 도입하고, MonetaryLedger의 채권 상환 처리 시 원금/이자를 분리하며, WorldState의 M2 집계 범위를 시스템 주체(Central Bank, Public Manager, System)를 제외하도록 조정했습니다.

## 2. 🚨 Critical Issues
*해당 없음 (보안 위반 또는 심각한 권한 탈취/하드코딩 발견되지 않음)*

## 3. ⚠️ Logic & Spec Gaps
* **Float Incursion in MonetaryLedger**: `modules/government/components/monetary_ledger.py` 라인 85 주변에서 `amount = float(repayment_details["principal"])` 코드를 사용하고 있습니다. `SettlementSystem`에서는 `FloatIncursionError`를 발생시키며 엄격하게 integer(pennies) 타입을 강제하고 있는데, Ledger에서 float로 변환하여 합산하면 시스템 전반의 정수 기반 회계 무결성이 깨집니다. 이 부분은 반드시 `int()`로 캐스팅하여 처리해야 합니다.
* **State Mutation Leak (SSoT Bypass)**: `simulation/systems/central_bank_system.py`에서 `world_state.transactions` 리스트의 참조를 직접 전달받아, 내부에서 `self.transactions.append(tx)`로 전역 상태를 직접 수정하고 있습니다. 이는 Orchestrator를 거치지 않고 System 깊은 곳에서 전역 상태를 은밀하게 변경하는 행위로, [VIBE_CHECK_MANUAL.md]의 SSoT 준수 규칙을 명백히 위반하는 안티패턴입니다.

## 4. 💡 Suggestions
* **Event-Driven Transaction Bubbling**: `CentralBankSystem`이 `transactions` 리스트를 직접 주입받는 대신, `SettlementSystem`에서 트랜잭션이 성공적으로 생성되었을 때 시스템 전역의 Event Bus를 통해 이벤트를 방출하고, `WorldState`나 `Orchestrator`가 이를 구독하여 트랜잭션 큐에 추가하도록 구조를 리팩토링하는 것이 부채를 남기지 않는 올바른 설계입니다.
* **Robust ID Type Safety**: `world_state.py`에서 `str(holder.id) == str(ID_CENTRAL_BANK)`와 같은 임시방편(Duct-Tape)식 타입 변환 방어보다는, Agent ID의 타입을 명확히 정의(예: `AgentID` Type Hinting 강제)하고 시스템 초기화 시점에서 일관된 타입을 보장하는 것이 근본적인 해결책입니다.

## 5. 🧠 Implementation Insight Evaluation

* **Original Insight**: 
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue... To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions...
* **Reviewer Evaluation**:
  > M2 누수의 근본 원인을 깊은 콜스택(LLR 등)에서 발생하는 '유령 화폐(기록되지 않는 트랜잭션)'로 정확하게 진단한 점은 훌륭합니다. 그러나 이를 해결하기 위해 `WorldState.transactions`를 `CentralBankSystem`에 주입(Injection)하여 내부에서 전역 리스트를 변경(`.append`)하는 방식은, Orchestrator의 중앙 통제(SSoT)를 우회하는 **State Mutation Leak** 안티패턴에 해당합니다. 당장의 버그는 덮었지만 향후 동시성 문제나 디버깅 추적성을 해치는 기술 부채를 유발했습니다. 해결 방향은 맞으나 구현 방식에서 Vibe Check(설계 순수성) 기준을 통과하지 못합니다.

## 6. 📚 Manual Update Proposal (Draft)

* **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
* **Draft Content**:
```markdown
### [YYYY-MM-DD] CentralBankSystem State Mutation Leak (Transaction Injection Pattern)
- **현상 (Symptom)**: CentralBankSystem의 LLR 동작 등에서 발생하는 트랜잭션 누락(Ghost Money)을 방지하기 위해, WorldState.transactions 리스트의 레퍼런스를 직접 주입받아 시스템 내부에서 append 하는 방식을 취함.
- **원인 (Cause)**: SettlementSystem을 거쳐 생성되는 트랜잭션을 깊은 콜스택에서부터 Orchestrator 층위로 리턴하는 파이프라인(Event Bubbling)이 부재하여, 손쉽게 전역 상태를 직접 변경(Duct-Tape)하는 방법을 선택함.
- **결과/위험성 (Risk)**: Orchestrator가 아닌 System 컴포넌트가 전역 상태(WorldState)를 암묵적으로 수정(State Mutation Leak)하므로, SSoT(Single Source of Truth) 원칙을 훼손하고 상태 변경의 추적을 어렵게 만듦.
- **해결 방안 (Action Item)**: Event Bus 패턴을 도입하거나, `SettlementSystem.transfer()` 내부에서 `TransactionCreated` 이벤트를 발행하여 WorldState가 이를 안전하게 수집하도록 리팩토링해야 함. 또한, MonetaryLedger에서 Float 연산(`float(repayment_details["principal"])`)을 Integer(pennies) 기반으로 즉시 수정해야 함.
```

## 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)** 
- ⚠️ Vibe Check Fail (State Mutation Leak: `CentralBankSystem`이 전역 트랜잭션 큐를 직접 수정하여 SSoT를 위반함)
- ⚠️ Logic Gap (Float Incursion: `MonetaryLedger`에서 채권 상환 시 `amount = float(...)`를 사용하여 Settlement의 Integer Only 룰 위반 및 잠재적 부동소수점 오차 유발 우려)