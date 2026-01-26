# 🔍 Git Diff Review: Remediation TD-116, TD-117, TD-118

## 1. 🔍 Summary

이 변경 사항은 시뮬레이션의 핵심 아키텍처를 개선하는 세 가지 중요한 기술 부채(TD-116, TD-117, TD-118)를 성공적으로 해결합니다.
- **TD-117 (DTO-Purity)**: `MarketSnapshotDTO`와 `GovernmentPolicyDTO`를 도입하여, 의사결정 로직을 시장의 실시간 상태(Live State)와 분리했습니다. 이로써 결정 로직의 순수성(Purity)과 테스트 용이성이 크게 향상되었습니다.
- **TD-118 (Sacred Sequence)**: 소비 시스템(`CommerceSystem`)을 계획(Plan)과 실행(Finalize)의 2단계로 분리하여 트랜잭션 처리의 무결성을 강화하고, 행위자의 상태 변경 로직을 명확한 단계로 이전했습니다.
- **TD-116 (Inheritance Leak)**: 상속 자산 분배 시 발생하던 부동 소수점 정밀도 문제를 해결하여, 시스템 내 자산이 유실되거나 생성되지 않도록 Zero-Sum 원칙을 보장하는 로직을 구현했습니다.

## 2. 🚨 Critical Issues

- 발견되지 않았습니다. 보안 및 데이터 정합성 측면에서 우수한 변경입니다.

## 3. ⚠️ Logic & Spec Gaps

- **`AIDrivenHouseholdDecisionEngine`의 빈 예외 처리**:
  - **위치**: `simulation/decisions/ai_driven_household_engine.py`, `_place_buy_orders` 함수
  - **문제**: `market_snapshot.prices`에서 주식 ID를 파싱하는 `try-except` 블록이 `pass`로 구현되어 있습니다. 만약 키 형식이 예상과 다를 경우, 오류가 조용히 무시되어 투자 가능한 주식 목록에서 해당 주식이 누락될 수 있습니다.
  - **권장**: 오류가 발생했을 때 디버깅이 가능하도록 최소한 `logger.warning`을 통해 예외 상황을 기록해야 합니다.

- **`TickScheduler`의 암묵적 폴백(Fallback) 값 사용**:
  - **위치**: `simulation/tick_scheduler.py`, `_phase_decisions` 함수
  - **문제**: `GovernmentPolicyDTO`를 생성할 때 `hasattr` 체크 후 폴백 값(e.g., `income_tax_rate: ... else 0.1`)을 사용합니다. 이는 시스템의 안정성을 높이지만, `government`나 `bank` 객체가 필요한 속성을 갖지 않는 설정 오류를 은폐할 수 있습니다.
  - **권장**: 폴백 값이 사용될 때 `logger.warning`을 기록하여, 설정이 잘못되었을 가능성을 운영자가 인지할 수 있도록 하는 것이 좋습니다.

## 4. 💡 Suggestions

- **`household_time_allocation` 데이터 흐름 개선**:
  - **위치**: `simulation/tick_scheduler.py`, `_phase_lifecycle` 함수
  - **제안**: 현재 `commerce_context`를 재구성하기 위해 `household_time_allocation` 데이터를 `self.world_state`에서 `getattr`로 가져오고 있습니다. 이는 `SimulationState` DTO의 설계 원칙을 약간 우회하는 방식입니다. 장기적으로는 `household_time_allocation`을 `SimulationState` DTO의 정식 필드로 추가하여, `_phase_lifecycle`에 명시적으로 전달하는 구조로 리팩토링하는 것을 고려해볼 수 있습니다.

## 5. 🧠 Manual Update Proposal

이번 변경 사항에서 도출된 중요한 아키텍처 원칙들을 문서화하여 프로젝트의 지식 자산으로 삼을 것을 제안합니다.

- **Target File**: `design/platform_architecture.md`
- **Update Content**:
  ```markdown
  ## 3. Core Architectural Patterns
  
  ### 3.1 Data-Driven Purity (DTOs for Decisions)
  
  - **현상**: 의사결정 로직(Decision Engine)이 실시간으로 변하는 Market 객체에 직접 접근하여 상태를 변경하거나 예측 불가능한 결과를 초래하는 문제.
  - **원칙**: 모든 의사결정 로직은 반드시 특정 시점의 불변 데이터 스냅샷(`DTO`, e.g., `MarketSnapshotDTO`)에 의존해야 한다. Market 객체와 같은 Live State 객체를 직접 주입하는 것을 금지한다.
  - **효과**:
      - **순수성**: 의사결정 함수는 Side-Effect를 일으키지 않으며, 동일 입력에 대해 항상 동일 출력을 보장한다.
      - **테스트 용이성**: 다양한 시나리오의 DTO를 생성하여 단위 테스트를 쉽게 작성할 수 있다.
      - **디버깅**: 특정 Tick의 `MarketSnapshotDTO`를 로깅하면, 해당 시점의 모든 결정 과정을 정확히 재현할 수 있다.
  
  ### 3.2 Two-Phase State Transition (Plan & Finalize)
  
  - **현상**: 단일 함수 내에서 상태 조회, 의사결정, 상태 변경이 뒤섞여 있어 로직 추적이 어렵고 동시성 문제가 발생할 수 있는 경우. (e.g., 소비를 결정하고 즉시 재고를 차감하는 경우)
  - **원칙**: 상태 변경이 포함된 복잡한 로직은 **계획(Plan)**과 **실행(Finalize)**의 두 단계로 분리한다.
      1.  **Phase 1 (Plan)**: 현재 상태를 바탕으로 모든 행위자(Agent)의 의도(Intent)나 트랜잭션(Transaction)을 생성하여 리스트에 담는다. 이 단계에서는 절대 상태를 변경하지 않는다.
      2.  **Phase 2 (Finalize/Process)**: 생성된 모든 트랜잭션과 의도를 중앙 처리기(e.g., `TransactionProcessor`)에서 일괄적으로 처리하여 상태를 변경한다.
  - **효과**:
      - **원자성(Atomicity)**: Tick 내의 모든 결정이 내려진 후 한 번에 상태 변경이 일어나므로 일관성이 유지된다.
      - **가시성**: `plan` 단계에서 생성된 트랜잭션 목록만 보면 해당 Tick에서 어떤 일이 일어날지 명확히 알 수 있다.
  
  ### 3.3 Financial Calculation Integrity (Zero-Sum Distribution)
  
  - **현상**: 다수에게 자산을 분배할 때, 부동 소수점 나눗셈으로 인해 총합이 미세하게 달라져 자산이 증발하거나 생성되는 버그.
  - **원칙**: 자산 분배 시, N-1명에게는 `floor` (또는 `round`) 처리된 금액을 분배하고, 마지막 1명에게는 `(총액 - 이미 분배된 금액)`을 할당하여 총합의 무결성을 강제한다.
  - **예시 (상속)**: `total_cash`를 3명에게 분배할 때, 2명에게 `floor(total_cash / 3)`를 주고, 마지막 1명에게 `total_cash - (2 * floor(total_cash / 3))`를 준다.
  - **효과**: 시스템 내에서 자산의 총량이 완벽하게 보존(Zero-Sum)된다.
  ```

## 6. ✅ Verdict

**REQUEST_CHANGES**

전반적으로 매우 훌륭하고 중요한 아키텍처 개선입니다. 시스템의 안정성과 확장성을 크게 향상했습니다. 위에 언급된 사소한 로깅 및 예외 처리 문제(`⚠️ Logic & Spec Gaps`)들을 수정한 후 머지하는 것을 강력히 권장합니다.
