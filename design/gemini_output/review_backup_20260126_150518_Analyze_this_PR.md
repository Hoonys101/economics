# 🔍 Git Diff Review: WO-121 Newborn Initialization

---

### 1. 🔍 Summary
이 변경은 시뮬레이션에서 새로 생성된 가계(신생아)가 빈 욕구(`needs`)를 가지고 초기화되던 버그를 수정합니다. 이제 신생아는 생존, 사회, 자산 등 필수적인 초기 욕구 값을 부여받아 생성 직후부터 경제 활동에 참여할 수 있습니다. 이를 검증하기 위한 단위 테스트가 추가되었습니다.

### 2. 🚨 Critical Issues
- 발견되지 않았습니다. 보안 및 데이터 무결성 관련 Critical 이슈는 없습니다.

### 3. ⚠️ Logic & Spec Gaps
- **하드코딩된 설정값**: `demographic_manager.py`의 `process_births` 메서드 내부에 `initial_needs_for_newborn` 딕셔너리가 하드코딩되어 있습니다. (L154-L162)
  - **문제점**: 이 값들은 시뮬레이션의 핵심 파라미터로, 로직 내부에 있을 경우 추후 수정 및 관리가 어렵습니다. 이는 아키텍처 원칙에 위배될 수 있습니다.
  - **영향**: 시나리오 변경이나 밸런스 조정을 위해 코드를 직접 수정해야 합니다.

- **테스트의 취약성(Brittleness)**: `tests/systems/test_demographic_manager_newborn.py`의 `demographic_manager_context` فিক্স처는 약 40줄에 걸쳐 시뮬레이션 설정값을 하드코딩하고 있습니다.
  - **문제점**: 향후 설정(config) 파일의 파라미터 이름이 변경되거나 기본값이 바뀔 경우, 이 테스트는 직접적인 관련이 없음에도 실패할 가능성이 매우 높습니다.
  - **영향**: 테스트의 유지보수 비용을 증가시키고, 설정 변경 시 불필요한 테스트 실패를 유발합니다.

### 4. 💡 Suggestions
1.  **설정값 외부화 (Configuration Externalization)**:
    - `demographic_manager.py`에 하드코딩된 `initial_needs_for_newborn` 딕셔너리를 `config/economy_params.yaml` 또는 유사한 설정 파일로 옮기는 것을 강력히 권장합니다.
    - DemographicManager는 시작 시 이 설정값을 주입받아 사용해야 합니다.
    - **예시 (`economy_params.yaml`):**
      ```yaml
      newborn_initial_needs:
        survival: 60.0
        social: 20.0
        improvement: 10.0
        asset: 10.0
        imitation_need: 15.0
        labor_need: 0.0
        liquidity_need: 50.0
      ```

2.  **테스트 리팩토링 (Test Refactoring)**:
    - 테스트 픽스처에서 모든 설정값을 하드코딩하는 대신, 기본 설정을 로드하고 이 테스트에 필수적인 값만 `MagicMock`을 통해 오버라이드하는 방식을 사용하는 것이 좋습니다. 이는 테스트를 더 견고하고 유지보수하기 쉽게 만듭니다.

### 5. 🧠 Manual Update Proposal
- **Target File**: `AGENTS.md`
- **Update Content**: `Household` 에이전트 섹션에 다음 원칙을 추가하여, 에이전트의 생명주기 설계에 대한 이해를 돕습니다.

  ```markdown
  ---
  ### Principle: Newborn Agent Initialization

  *   **현상 (Phenomenon)**: 새로 생성된 에이전트(신생아)가 경제 활동에 참여하지 않고 빠르게 도태되었습니다.
  *   **원인 (Cause)**: 에이전트의 `needs` 딕셔너리가 빈 상태(`{}`)로 초기화되어, 행동을 유발할 동기(motivation)가 전혀 없었습니다.
  *   **해결 (Solution)**: 에이전트 생성 시점에서 생존, 사회적 욕구 등 행동에 필수적인 최소한의 초기 `needs` 값을 주입합니다.
  *   **교훈 (Lesson)**: 모든 에이전트는 반드시 행동의 기반이 되는 초기 상태(욕구, 자산 등)를 가져야 합니다. '진공 상태'의 에이전트는 시뮬레이션의 안정성을 해치는 요인이 됩니다.
  ---
  ```

### 6. ✅ Verdict
**REQUEST CHANGES**

이유: 변경의 핵심 로직은 올바르며 버그를 해결하는 중요한 수정입니다. 하지만 `initial_needs_for_newborn` 값을 코드 내에 하드코딩한 것은 프로젝트의 아키텍처 가이드라인에 위배됩니다. 제안된 바와 같이 해당 값을 설정 파일로 분리하여 코드의 유연성과 유지보수성을 확보한 후 다시 리뷰를 요청해주십시오.
