# Code Review Report

## 1. 🔍 Summary
`CentralBankSystem`이 LLR(최종대부자) 역할 등에서 발행하는 부수효과 통화를 집계하기 위해 전역 트랜잭션 큐(`world_state.transactions`)를 직접 주입받아 사용하도록 수정되었습니다. 또한 `WorldState`의 M2 집계 기준에서 시스템 에이전트들을 제외하고, `MonetaryLedger`에서 채권 원금/이자 상환 분리를 지원합니다.

## 2. 🚨 Critical Issues
- **Global State Mutation Leak (State Bypass)**: `SimulationInitializer`에서 `CentralBankSystem`에 `sim.world_state.transactions` 리스트의 참조를 직접 주입하고, `mint_money` 등에서 `self.transactions.append(tx)`로 전역 상태를 직접 수정하는 것은 아키텍처 원칙을 심각하게 위반하는 "State Mutation Leak"입니다. 모든 상태 변경(트랜잭션 기록)은 엔진/시스템이 직접 하는 것이 아니라, 실행 결과(`Transaction` 객체)를 반환(Return)하여 호출자인 Orchestrator나 Agent 계층에서 수집 및 처리하도록 강제해야 합니다.

## 3. ⚠️ Logic & Spec Gaps
- **Duct-Tape Debugging (문자열 형변환)**: `WorldState.calculate_total_money`에서 `str(holder.id) == str(ID_CENTRAL_BANK)`와 같이 모든 ID를 문자열로 강제 변환하여 비교하는 것은 타입 불일치를 덮기 위한 임시방편(Duct-Tape)입니다. Agent 생성 시점에 ID의 타입을 명확히 강제하고 보장해야 합니다.
- **Float Incursion Risk**: `MonetaryLedger.process_transactions` 내 채권 상환 처리 시 `amount = float(repayment_details["principal"])`와 같이 `float`으로 캐스팅하는 로직이 추가되었습니다. 금융/결제 정합성 체크 시 `int`(Pennies) 타입을 요구하고 있으므로, `float` 캐스팅은 `expected_m2_pennies` 등 핵심 통화량 변수의 타입을 오염시킬 위험이 있습니다.

## 4. 💡 Suggestions
- `CentralBankSystem`의 `mint_money`, `transfer_and_burn` 등의 메서드가 `bool`만 반환하거나 내부에서 직접 큐에 삽입하는 대신, 성공 시 생성된 `Transaction` 객체(또는 `None`)를 반환하도록 시그니처를 수정하십시오.
- `WorldState`의 집계 로직에서 `str()` 캐스팅을 제거하고, 시스템 전반의 `AgentID` 타입을 단일화(`int` 또는 `str`)하는 리팩토링을 수행하십시오.
- `repayment_details["principal"]` 추출 시 `float` 대신 `int`로 변환하여 시스템 내 금액 단위(Pennies)와의 정합성을 일치시키십시오.

## 5. 🧠 Implementation Insight Evaluation
- **Original Insight**:
  > The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. ... To fix this, we implemented a Transaction Injection Pattern for the CentralBankSystem. By injecting the WorldState.transactions list into the CentralBankSystem upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. ... ID comparisons were also robustified using string conversion to preventing type mismatch errors.
- **Reviewer Evaluation**: 인사이트에 기술된 문제 원인 파악(LLR 등 부수효과 통화가 트랜잭션 기록에 누락됨)은 매우 정확합니다. 하지만 이를 해결하기 위해 도입한 "Transaction Injection Pattern"은 사실상 전역 큐를 직접 조작하는 안티패턴으로, SSoT(Single Source of Truth) 접근 원칙을 심각하게 훼손합니다. 또한, "ID comparisons were also robustified using string conversion"이라는 주장은 타입 시스템의 불일치라는 기술 부채를 단순히 은폐하는 "Vibe Check Fail"에 해당합니다. 근본적인 타입 정합성 개선이 누락된 잘못된 교훈입니다.

## 6. 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
```markdown
### [WO-WAVE5-MONETARY-FIX] State Mutation Leak & Duct-Tape Type Casting
- **현상**: `CentralBankSystem`에서 전역 상태인 `world_state.transactions` 리스트를 참조 주입(Injection)받아 직접 수정(Append)하는 패턴이 도입됨. 또한 Agent ID 비교 시 타입 불일치를 무마하기 위해 런타임에 `str()` 형변환을 남발함.
- **원인**: 깊은 콜스택(LLR 실행 등) 내부에서 발생하는 부수효과 트랜잭션을 상위로 명시적으로 반환(Return)하기 번거로워 전역 큐를 직접 조작하는 우회로(Bypass)를 선택함. ID의 경우 Agent 초기화 과정에서 일관된 타입 강제가 부재하여 땜질식 처방을 함.
- **해결 (Action Item)**: 
  1. 시스템/엔진 클래스는 전역 상태 리스트의 직접 참조를 제거하고, 발생한 `Transaction` 객체를 반환값(Return)으로 상위에 전달하여 Orchestrator가 취합하도록 리팩토링할 것.
  2. `AgentID` 타입을 단일 규격(`int` 또는 `str`)으로 통일하고, DTO 및 Entity 생성 시점에 엄격한 타입 검증 로직을 추가할 것.
  3. 금액(Amount) 관련 변수는 오차를 유발하는 `float` 형변환을 금지하고 `int`(Pennies) 규격을 강제할 것.
- **교훈**: 편의를 위한 전역 상태 주입(Transaction Injection Pattern)은 예측 불가능한 부수효과를 낳으며 SSoT를 훼손한다. 모든 상태 변경은 함수형 원칙(Return & Aggregate)에 따라 투명하게 추적되어야 하며, 타입 문제는 캐스팅으로 덮지 말고 근본 스키마를 수정해야 한다.
```

## 7. ✅ Verdict
- **REQUEST CHANGES (Hard-Fail)**
  - **⚠️ Vibe Check Fail**: SSoT를 우회하는 전역 트랜잭션 리스트 직접 주입 및 수정 (State Mutation Leak).
  - **⚠️ Vibe Check Fail**: 근본적인 타입 불일치를 덮어버리는 땜질식 문자열 형변환 (`str(holder.id) == str(ID_CENTRAL_BANK)`).