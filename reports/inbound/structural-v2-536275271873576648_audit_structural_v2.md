# AUDIT_SPEC_STRUCTURAL Report (v2.0)

**작성자**: Jules (Senior System Architect)
**날짜**: 2024-05-22 (Simulated)
**대상**: 전체 코드베이스 및 구조적 무결성

---

## 1. 개요 (Overview)
본 보고서는 'design/specs/AUDIT_SPEC_STRUCTURAL.md'에 명시된 SoC(Separation of Concerns) 원칙 및 구조적 무결성 기준에 따라 프로젝트를 감수한 결과입니다. 주요 검증 항목은 God Class 식별, Leaky Abstraction 탐지, 그리고 Sacred Sequence 준수 여부입니다.

## 2. God Class 식별 (God Class Identification)
**기준**: 800라인 이상 또는 3개 이상의 도메인 책임 혼재.

### 탐지 결과
- **파일명**: `simulation/core_agents.py`
- **라인 수**: 840 Lines
- **분석**:
  - 해당 파일의 `Household` 클래스는 생물학적(Bio), 경제적(Econ), 사회적(Social) 로직을 모두 Facade 패턴으로 위임하고 있으나, 여전히 레거시 로직과 위임 코드가 혼재되어 비대해졌습니다.
  - 특히 `create_state_dto`, `make_decision` 등 주요 메서드와 수많은 프로퍼티 델리게이션 코드가 클래스 크기를 증가시키는 주원인입니다.
  - **권고**: `Household` 클래스의 프로퍼티 위임 로직을 자동화하거나, 컴포넌트 접근을 `self.bio`, `self.econ` 등으로 직접 노출하는 방식을 고려하여 Facade의 두께를 줄여야 합니다.

## 3. Leaky Abstraction 탐지 (Leaky Abstraction Detection)
**기준**: `DecisionContext` 초기화 시 DTO가 아닌 에이전트 인스턴스(`self`)를 직접 전달하는 경우.

### 탐지 결과
1. **`simulation/core_agents.py` (Line 674)**
   ```python
   context = DecisionContext(
       household=self, # COMPATIBILITY RESTORED: Required for RuleBasedHouseholdDecisionEngine
       ...
   )
   ```
   - **문제점**: `Household` 인스턴스(`self`)가 `DecisionContext`에 직접 주입되고 있습니다. 이는 의사결정 엔진이 에이전트의 내부 상태를 직접 변경할 수 있는 경로를 열어두어 Purity Gate 원칙을 위반합니다.

2. **`simulation/firms.py` (Line 326)**
   ```python
   context = DecisionContext(
       firm=self,
       ...
   )
   ```
   - **문제점**: `Firm` 인스턴스 또한 동일하게 직접 주입되고 있습니다.

### 권고 사항
- `DecisionContext` 정의에서 `household` 및 `firm` 필드를 제거하고, 오직 `HouseholdStateDTO`, `FirmStateDTO`만을 받도록 강제해야 합니다.
- 현재 주석에 "COMPATIBILITY RESTORED"라고 명시된 것으로 보아, 구형 Rule-Based 엔진들이 DTO가 아닌 객체에 의존하고 있는 것으로 파악됩니다. 해당 엔진들의 리팩토링이 선행되어야 합니다.

## 4. Sacred Sequence 검증 (Sacred Sequence Verification)
**기준**: `Decisions -> Matching -> Transactions -> Lifecycle` 실행 순서 준수.

### 검증 결과
- **파일명**: `simulation/tick_scheduler.py`
- **검증**: `run_tick` 메서드 내의 실행 흐름을 분석한 결과, 다음 순서가 명확히 준수되고 있음을 확인했습니다.
  1. **Decisions**: `self._phase_decisions(sim_state, ...)`
  2. **Matching**: `self._phase_matching(sim_state)`
  3. **Transactions**: `self._phase_transactions(sim_state)`
  4. **Lifecycle**: `self._phase_lifecycle(sim_state)`
- **결론**: **PASS**. `tick_scheduler.py`는 구조적 순서를 올바르게 강제하고 있습니다.

---

## 5. 종합 결론 (Conclusion)
시스템은 전반적으로 `tick_scheduler.py`를 통해 강력한 실행 순서 제어권을 가지고 있으나, 개별 에이전트(`Household`, `Firm`) 수준에서는 여전히 과도한 책임 집중(God Class)과 캡슐화 누수(Leaky Abstraction)가 발생하고 있습니다.

특히 `DecisionContext`에 `self`를 넘기는 행위는 향후 병렬 처리나 엔진 교체 시 사이드 이펙트를 유발할 수 있는 치명적인 기술 부채입니다. 이를 해결하기 위해 WO-108(Parity & DTO Compliance) 작업의 가속화가 필요합니다.