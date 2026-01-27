# 🔍 Git Diff Review Report

## 1. 🔍 Summary
이 변경 사항은 `Household` 에이전트 생성 시 발생하는 속성 설정 오류(Attribute Error)를 해결하기 위한 것입니다. 이를 위해 `Household` 클래스의 여러 속성에 public setter를 추가하고, 신규 에이전트의 `desire_weights`를 `AITrainingManager`에서 직접 설정하도록 로직을 수정했습니다. 또한, `DecisionContext`에서 `markets`와 `government` 객체를 제거하여 의존성을 개선하는 리팩토링이 포함되었습니다.

## 2. 🚨 Critical Issues
- 해당 사항 없음.

## 3. ⚠️ Logic & Spec Gaps
- **[CRITICAL] 아키텍처 위반: Agent 캡슐화 파괴**
  - **위치**: `simulation/core_agents.py`
  - **내용**: `age`, `personality`, `generation`, `current_consumption` 등 `Household` 에이전트의 핵심 상태를 나타내는 거의 모든 속성에 public setter(`@<property>.setter`)가 추가되었습니다.
  - **문제점**: 이 변경은 에이전트의 내부 상태를 외부에서 아무런 제약 없이 수정할 수 있게 만듭니다. 이는 객체지향의 핵심 원칙인 **캡슐화를 심각하게 위반**하는 행위입니다. 에이전트는 더 이상 자신의 상태를 스스로 관리하는 자율적인 주체가 아니라, 외부 코드에 의해 쉽게 상태가 오염될 수 있는 단순한 데이터 묶음(Data Bag)으로 전락합니다. 이는 장기적으로 예측 불가능한 버그와 유지보수 비용 급증의 원인이 됩니다. `AttributeError`를 해결하기 위해 사용된 이 방법은 근본적인 해결책이 아니며 더 큰 기술 부채를 유발합니다.

- **관심사 분리(SoC) 원칙 위배 가능성**
  - **위치**: `simulation/ai/ai_training_manager.py`, line 73-83
  - **내용**: 이전에는 `child_agent.psychology._initialize_desire_weights(...)`를 통해 `psychology` 컴포넌트가 담당했던 '욕구 가중치' 초기화 로직이 `AITrainingManager` 내부로 이동하고 하드코딩 되었습니다.
  - **문제점**: 에이전트의 '심리'와 관련된 로직이 'AI 훈련 관리자'에 직접 구현되는 것은 관심사 분리 원칙에 어긋날 수 있습니다. `AITrainingManager`는 훈련 프로세스를 총괄하는 역할을 맡고, 심리 모델의 구체적인 초기화는 `psychology` 모듈이 책임지는 것이 더 적절한 설계입니다.

## 4. 💡 Suggestions
- **Setter 추가 대신 명시적 메서드(Method) 제공**
  - `core_agents.py`에 추가된 모든 setter를 제거하십시오.
  - 대신, 상태를 변경해야 하는 명확한 의도를 드러내는 메서드를 `Household` 클래스에 추가하는 것을 강력히 권장합니다. 예를 들어, 신규 에이전트 생성 시 속성을 설정해야 한다면 아래와 같은 메서드를 고려할 수 있습니다.
    ```python
    # In Household class
    def initialize_as_child(self, parent_agent: 'Household', personality: Personality, initial_desire_weights: Dict[str, float]):
        """A new agent is born or created."""
        self.parent_id = parent_agent.id
        self.generation = parent_agent.generation + 1
        self.age = 0
        self.personality = personality
        self.desire_weights = initial_desire_weights
        # ... other initializations
    ```
  - 이렇게 하면 `AITrainingManager`는 `child_agent.initialize_as_child(...)`를 호출하여, 상태 변경의 책임을 `Household` 에이전트 자신에게 위임하게 됩니다. 이는 훨씬 더 견고하고 안정적인 설계입니다.

- **`DecisionContext` 리팩토링**
  - `simulation/core_agents.py`와 `simulation/firms.py`에서 `DecisionContext` 생성 시 `markets`, `government` 같은 거대 객체 참조를 제거한 것은 의존성을 줄이고 결합도를 낮추는 좋은 변경입니다. 이 방향은 유지하는 것이 좋습니다.

## 5. 🧠 Manual Update Proposal
- **Target File**: `design/개발지침.md`
- **Update Content**: "에이전트 설계 원칙" 섹션에 다음 내용을 추가하여 유사한 실수를 방지하도록 가이드해야 합니다.

  ```markdown
  ---
  ### **[Anti-Pattern] `AttributeError` 해결을 위한 무분별한 Setter 추가**

  - **현상**: 외부 모듈에서 에이전트의 속성을 수정하려 할 때 `AttributeError: can't set attribute` 오류가 발생하자, 이를 해결하기 위해 해당 속성에 `@property.setter`를 추가한다.
  - **문제점**: 이는 에이전트의 내부 상태를 외부에 완전히 노출시켜 캡슐화를 파괴하는 행위입니다. 에이전트의 상태 일관성이 깨지기 쉬워지며, 시스템 전체의 복잡도와 버그 발생 가능성을 높이는 주요 기술 부채가 됩니다.
  - **해결책**:
    1.  **Setter 추가를 지양**하고, 해당 속성 변경이 꼭 필요한지 설계 자체를 다시 검토합니다.
    2.  상태 변경이 반드시 필요하다면, **변경의 '의도'가 명확히 드러나는 메서드를 제공**하십시오. (예: `agent.age = 10` (X) -> `agent.age_by(10)` (O), `agent.personality = X` (X) -> `agent.develop_personality(X)` (O))
    3.  이를 통해 에이전트는 자기 자신의 상태 변경을 스스로 통제할 수 있으며, 외부에서는 정해진 인터페이스(메서드)를 통해서만 상태에 영향을 줄 수 있어 훨씬 안정적인 구조가 됩니다.
  ---
  ```

## 6. ✅ Verdict
**REQUEST CHANGES**

**이유**: 핵심 에이전트인 `Household`의 캡슐화를 심각하게 훼손하는 구조적 결함이 발견되었습니다. 이는 단기적으로 문제를 해결하는 것처럼 보이나, 장기적으로 프로젝트의 안정성과 유지보수성을 크게 저해할 것입니다. 제안된 내용에 따라 아키텍처를 수정한 후 다시 리뷰를 요청해주십시오.
