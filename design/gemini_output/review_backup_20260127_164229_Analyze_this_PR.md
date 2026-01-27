# 🔍 Git Diff Review: `fix-household-attribute-error`

## 🔍 Summary

이 변경 사항은 `Household` 에이전트의 상태 관리 방식을 대대적으로 리팩토링합니다. 여러 외부 시스템(`Registry`, `TickScheduler` 등)이 에이전트의 속성을 직접 수정하던 기존 방식에서, 에이전트가 자체 상태를 관리하는 명시적인 메서드(`record_consumption`, `reset_consumption_counters` 등)를 제공하는 방식으로 변경되었습니다. 이는 캡슐화와 단일 책임 원칙(SoC)을 강화하여 코드의 안정성과 유지보수성을 크게 향상시킵니다.

## 🚨 Critical Issues

- **None**: 보안 위반, 민감 정보 하드코딩, 제로섬 위반 등의 심각한 문제는 발견되지 않았습니다.

## ⚠️ Logic & Spec Gaps

- **[Minor] 로직 파라미터 하드코딩**: `simulation/ai/ai_training_manager.py`의 `mitosis` 함수 내에서, 새로 태어난 에이전트의 성격(Personality)에 따른 욕구 가중치(`weights`)가 딕셔너리 형태로 하드코딩되었습니다.
  ```python
  # L70-77 in ai_training_manager.py
  if new_personality in [Personality.MISER, Personality.CONSERVATIVE]:
      weights = {"survival": 1.0, "asset": 1.5, ...}
  ```
  이는 기능적으로는 문제가 없으나, 핵심 게임 로직 파라미터를 소스 코드에 직접 두는 것은 향후 밸런스 조정 및 튜닝을 어렵게 만듭니다. 이 가중치 값들은 `config/economy_params.yaml` 같은 설정 파일로 분리하여 관리하는 것을 권장합니다.

## 💡 Suggestions

- **[Code Style] 불필요한 컨텍스트 파라미터 제거**: `simulation/core_agents.py` 와 `simulation/firms.py`에서 `DecisionContext` 생성 시 사용되지 않는 `markets`, `government` 파라미터를 제거한 것은 좋은 정리입니다. 이 패턴을 프로젝트 전반의 다른 `DecisionContext` 생성 지점에도 적용하여 일관성을 유지하는 것을 고려해볼 수 있습니다.
- **[Testability] 테스트 Mock 객체 인터페이스 준수**: `simulation/tick_scheduler.py`에서 `reset_consumption_counters` 메서드가 없는 객체를 위한 폴백(fallback) 로직이 추가되었습니다. 이는 테스트 환경에서의 안정성을 높여주지만, 장기적으로는 테스트용 Mock 객체들도 실제 객체와 동일한 인터페이스(즉, `reset_consumption_counters` 메서드)를 구현하도록 업데이트하여 코드의 복잡성을 줄이는 것이 더 이상적입니다.

## 🧠 Manual Update Proposal

이번 변경 사항은 프로젝트의 핵심 설계 원칙을 잘 보여주는 중요한 사례입니다.

- **Target File**: `design/platform_architecture.md` (또는 `design/개발지침.md`)
- **Update Content**: 다음 섹션을 추가하여 "Tell, Don't Ask" 원칙을 공식화할 것을 제안합니다.

  ---
  ### **아키텍처 패턴: 에이전트 상태 캡슐화 (Tell, Don't Ask)**

  - **현상 (Problem)**: `TickScheduler`, `Registry`와 같은 외부 관리 시스템이 `Household`와 같은 에이전트의 내부 상태 속성(`household.current_consumption = 0`)을 직접 조회하고 수정했습니다. 이는 시스템 간의 강한 결합(high coupling)을 유발하고 캡슐화를 위반하며, 에이전트를 단순한 데이터 묶음(Data Bag)으로 전락시켜 상태 관리의 일관성을 해칠 위험이 있습니다.

  - **해결책 (Solution)**: 에이전트는 자신의 상태를 관리하기 위한 명시적인 공개 메서드(e.g., `household.reset_consumption_counters()`, `household.record_consumption(...)`)를 외부에 제공해야 합니다. 외부 시스템은 에이전트의 데이터를 직접 수정하는 대신, 에이전트에게 "무엇을 할지"를 **'명령(Tell)'**해야 합니다.

  - **기대효과 (Benefit)**:
      1.  **유지보수성 향상**: 에이전트의 상태 변경 로직이 클래스 내로 중앙화되어 코드 수정이 용이해집니다.
      2.  **안정성 강화**: 외부에서 에이전트의 상태를 임의로 변경할 수 없으므로, 얘기치 않은 버그 발생 가능성이 줄어듭니다.
      3.  **API 명확성**: 에이전트의 공개 API가 명확해져 다른 개발자가 에이전트를 더 쉽고 안전하게 사용할 수 있습니다.

  ---

## ✅ Verdict

**APPROVE**

전체적인 코드 구조를 크게 개선하는 매우 긍정적인 변경입니다. 제안된 사항들은 코드 품질을 더욱 높이기 위한 권장 사항이며, 머지를 막을 이유는 없습니다.
