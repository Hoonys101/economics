# 🐙 Gemini CLI System Prompt: Git Reviewer Report

## 1. 🔍 Summary
이 PR은 `AgentRegistry`를 강화하여 `ISystemAgentRegistry` 인터페이스를 도입하고, 시스템 에이전트(중앙은행, 공공관리자 등)의 명시적 등록을 지원합니다. 특히 `0`과 같은 Falsy ID가 무시되거나 누락되는 버그(`if agent:` -> `if agent is not None:`)를 수정하였으며, 테스트 코드의 ID 충돌(Household ID `1`과 Government ID `1` 충돌)을 올바르게 해결했습니다.

## 2. 🚨 Critical Issues
*   **None**: 보안 위반, 하드코딩, 또는 자원 복사(Zero-Sum 위반) 문제는 발견되지 않았습니다.

## 3. ⚠️ Logic & Spec Gaps
*   **None**: 변경 사항은 기획 의도에 완벽히 부합하며, Registry의 상태 무결성을 훼손하지 않습니다.

## 4. 💡 Suggestions
*   **Insight Report Format**: 작성된 `WO-IMPL-MODULAR-SYSTEM.md`의 내용이 훌륭하지만, 추후 공식 매뉴얼 반영의 용이성을 위해 `현상(Phenomenon) / 원인(Cause) / 해결(Solution) / 교훈(Lesson)`의 표준 템플릿 구조를 도입하는 것을 권장합니다.

## 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**: 
    > **Falsy ID Handling**: The explicit check `if agent_id is None` replaces implicit falsy checks (`if not agent_id`), preventing the "Agent 0 Disappearance" bug. This is a critical hardening pattern for any system using integer IDs starting at 0.
    > **Test Failure in `test_audit_total_m2_logic`**: The existing test mocked a `Household` with `id=1`. However, `ID_GOVERNMENT` is defined as `1` in `modules/system/constants.py`.
*   **Reviewer Evaluation**: Jules가 작성한 인사이트는 매우 타당하며 기술적 깊이가 있습니다. 시스템 에이전트들의 고정 ID(특히 ID `0`과 `1`)가 시뮬레이션 및 테스트 전반에 미치는 영향을 정확히 짚어냈습니다. `is None` 명시적 타입 검사는 파이썬에서 정수 `0`을 다룰 때 필수적인 방어 로직이며, 이를 통해 "Agent 0 (Central Bank) 증발" 문제를 영구적으로 해결했습니다. 

## 6. 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (또는 `ECONOMIC_INSIGHTS.md`)
*   **Draft Content**:
    ```markdown
    ### [Resolved] ID 0 (Central Bank) Falsy Evaluation Bug & Test Collisions
    - **현상 (Phenomenon)**: 중앙은행(ID: 0)과 같은 시스템 에이전트가 Registry에서 조회되지 않거나, M2 통화량 검증 테스트가 의문스럽게 실패하는 현상 발생.
    - **원인 (Cause)**: 
      1. 파이썬의 암묵적 Falsy 검사(`if not agent_id:` 또는 `if agent:`)로 인해 ID가 `0`인 경우 유효하지 않은 값으로 처리됨.
      2. 단위 테스트에서 일반 가계(Household)의 ID를 `1`로 모킹(Mocking)하였으나, 이는 `ID_GOVERNMENT = 1`과 충돌하여 정부 자산으로 오인됨.
    - **해결 (Solution)**: 
      - `AgentRegistry`의 조회 로직을 `if agent_id is None:` 및 `if agent is not None:`으로 명시적 변경.
      - `ISystemAgentRegistry`를 분리하여 시스템 에이전트 전용 등록 채널(`register_system_agent`) 신설.
      - 테스트 픽스처의 더미 에이전트 ID를 100 이상(예: 101)으로 할당하여 시스템 예약 ID(0~99)와의 충돌 원천 차단.
    - **교훈 (Lesson)**: 시스템 전역에서 ID 식별자를 다룰 때는 **반드시 `is None` 명시적 비교를 사용**해야 하며, 테스트 코드 작성 시 **예약된 상수 ID 영역(0~100)을 침범하지 않도록 주의**해야 합니다.
    ```

## 7. ✅ Verdict
**APPROVE**
(보안 및 로직 무결성이 확인되었으며, 발생한 버그의 근본 원인을 해결하는 테스트 코드가 포함되어 있습니다. 인사이트 리포트 또한 요구사항에 맞게 잘 작성되었습니다.)