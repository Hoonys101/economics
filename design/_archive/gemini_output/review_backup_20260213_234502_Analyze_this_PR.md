# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
`CommandService`의 Undo 로직을 전면 리팩토링하여 `RegistryEntry` 기반의 정밀한 롤백(Origin 및 Lock 상태 보존)을 구현했습니다. 섀도잉되어 작동하지 않던 `pop_commands` 메서드를 제거하고, `IRestorableRegistry` 프로토콜을 도입하여 `delete_entry`/`restore_entry` 명세를 확립했습니다.

## 🚨 Critical Issues
*   None found.

## ⚠️ Logic & Spec Gaps
*   None found. 구현이 명세 및 테스트 증거와 일치합니다.

## 💡 Suggestions
*   `tests/unit/modules/system/test_command_service_unit.py`에서 `mock_restorable_registry` 픽스처 생성 시 `spec=IRestorableRegistry`를 사용한 것은 훌륭한 방어적 코딩입니다.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: "Regressions in `test_god_command_protocol.py` revealed that `MockRegistry` was not fully compliant with `IGlobalRegistry` (missing `get_entry`). This was fixed by implementing the missing method, reinforcing the importance of mocks strictly adhering to protocols."
*   **Reviewer Evaluation**: 매우 중요한 통찰입니다. Mock 객체가 실제 프로토콜(Interface)과 괴리될 때 발생하는 '거짓 양성(False Positive)' 테스트 성공의 위험성을 정확히 지적했습니다. 이는 테스트 신뢰성 확보를 위한 핵심 원칙입니다.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/1_governance/architecture/standards/TESTING_STABILITY.md` (혹은 관련 테스팅 표준 문서)
*   **Draft Content**:
```markdown
### Mock Compliance & Protocol Fidelity
Mock 객체는 반드시 대상 Protocol(Interface)의 모든 메서드를 구현해야 합니다.
- **Rule**: `Protocol` 정의 시 `@runtime_checkable`을 사용하고, 테스트 픽스처에서 `isinstance(mock, Protocol)` 검증이나 `spec=Protocol` 옵션을 적극 활용하십시오.
- **Risk**: 부분적으로만 구현된 Mock은 통합 단계에서야 발견되는 `AttributeError`나 인터페이스 불일치 오류를 은폐할 수 있습니다 (예: `IGlobalRegistry`의 `get_entry` 누락 사례).
```

## ✅ Verdict
**APPROVE**