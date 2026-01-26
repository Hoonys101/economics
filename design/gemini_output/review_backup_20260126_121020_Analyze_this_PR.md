# 🔍 Git Diff Review: `fix-household-engine-nameerror`

---

### 1. 🔍 Summary
이 변경 사항은 `AIDrivenHouseholdDecisionEngine`에서 발생한 `NameError`를 `context.markets`를 사용하도록 수정하여 해결합니다. 또한, 테스트 코드를 리팩토링하여 새로운 `DecisionContext` 구조(state, config 포함)를 반영하고, live 객체 대신 직렬화된 `market_data`를 사용하는 아키텍처 변경에 맞게 테스트를 업데이트합니다.

### 2. 🚨 Critical Issues
- 발견되지 않았습니다.

### 3. ⚠️ Logic & Spec Gaps
- **Hardcoded Fallback Value**: `ai_driven_household_engine.py`의 356라인 근처에서, `mortgage_rate`의 fallback 값으로 `0.05`가 하드코딩되어 있습니다.
  ```python
  # L356
  mortgage_rate = market_data.get("loan_market", {}).get("interest_rate", 0.05)
  ```
  이 값은 테스트 코드(`tests/test_household_decision_engine_new.py`)에서 상세하게 설정되고 있는 다른 설정값들과 마찬가지로, `config` 모듈을 통해 관리되어야 합니다. 이는 'Magic Number'를 제거하고 설정의 중앙 관리를 가능하게 합니다.

### 4. 💡 Suggestions
- **Configuration Parameterization**: `0.05`라는 하드코딩된 값을 `config.DEFAULT_MORTGAGE_RATE`와 같은 설정 파라미터로 추출하고, `mock_config`에도 이 값을 추가하여 일관성을 유지하는 것을 제안합니다.

### 5. 🧠 Manual Update Proposal
- **Target File**: `design/platform_architecture.md`
- **Update Content**:
  - **새로운 원칙 추가 제안:** `Decision Engine 설계 원칙` 섹션에 다음 내용을 추가합니다.
    ```markdown
    ### 원칙 2: 의사결정 엔진의 순수성 (Purity of Decision Engines)

    **현상:** 의사결정 로직(예: `AIDrivenHouseholdDecisionEngine`)이 `market`과 같은 live 서비스 객체를 직접 참조하면서, 테스트가 복잡해지고 서비스 간 결합도가 높아지는 문제가 발생했습니다.

    **원인:** 엔진이 외부 상태(live object)에 직접 의존하여, 동일 입력에 대해 다른 결과를 낼 수 있는 비결정적 특성을 가집니다.

    **해결:** 의사결정 엔진은 반드시 `DecisionContext`를 통해 전달되는 정적 데이터(State DTO, Market Data, Config)에만 의존해야 합니다. 엔진 내부에서 live 서비스 객체의 메서드를 직접 호출해서는 안 됩니다. 필요한 모든 외부 상태 정보는 호출하는 쪽에서 `market_data`와 같은 직렬화 가능한 데이터 구조로 변환하여 `Context`에 담아 전달해야 합니다.

    **교훈:** 이 원칙은 의사결정 로직을 외부 서비스로부터 완전히 분리(decoupling)하여, 행위를 예측 가능하게 만들고 테스트 용이성을 극대화합니다. 엔진은 입력 데이터에 대해서만 작동하는 순수 함수(pure function)처럼 동작하게 됩니다.
    ```

### 6. ✅ Verdict
**REQUEST CHANGES**

**Reasoning:** 핵심적인 버그 수정은 정확하지만, 하드코딩된 'Magic Number'가 발견되었습니다. 제안된 대로 설정을 통해 관리하도록 수정이 필요합니다. 아키텍처 개선 방향은 매우 긍정적입니다.
