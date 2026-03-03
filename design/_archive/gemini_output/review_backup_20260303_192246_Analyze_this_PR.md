# Code Review Report

## 1. 🔍 Summary
이번 PR은 테스트 환경에서 발생하는 `MemoryError` 및 객체 수명 주기로 인한 메모리 누수를 해결합니다. `Government`와 `FinanceSystem` 간의 순환 참조를 `weakref.proxy`로 끊어내고, 누락된 모듈의 `MagicMock`이 무한 증식하는 것을 막기 위해 `ShallowModuleMock`을 도입했으며, 테스트 종료 시 명시적으로 트랜잭션 로그와 레지스트리 내부 상태를 초기화하도록 수정했습니다.

## 2. 🚨 Critical Issues
- **None**: 보안 위반, 하드코딩, 혹은 Zero-Sum 원칙을 위반하는 심각한 로직 오류는 발견되지 않았습니다.

## 3. ⚠️ Logic & Spec Gaps
- **Identity Broken in `ShallowModuleMock`**: `tests/conftest.py`에 추가된 `ShallowModuleMock`은 `__getattr__` 호출 시마다 새로운 `MagicMock(return_value=None)`을 반환합니다. 이는 동일한 속성에 여러 번 접근할 때 매번 다른 Mock 객체를 반환하게 하므로(예: `numpy.array is numpy.array`가 `False`가 됨), 테스트 내 객체 동일성 검증이나 참조 로직이 깨질 위험이 있습니다.
- **Function-scoped Mock Leaks**: `tests/integration/scenarios/diagnosis/conftest.py`의 `clean_room_teardown`에서 `mock_agent_registry.agents.clear()`를 명시적으로 호출하고 있습니다. `mock_agent_registry`는 함수 스코프(`@pytest.fixture`)이므로 테스트 종료 시 자연스럽게 소멸(GC)되어야 합니다. 이것을 수동으로 비워야만 메모리가 안정된다면, 테스트 프레임워크 어딘가에 이 Mock을 참조하는 **글로벌 참조 누수(Global Reference Leak)** 가 여전히 존재한다는 뜻입니다.

## 4. 💡 Suggestions
- **Refine `ShallowModuleMock`**: 반환된 Mock을 캐싱하여 Identity를 보장하도록 수정하십시오.
  ```python
  class ShallowModuleMock(MagicMock):
      def __getattr__(self, name):
          if name.startswith("_"):
              return super().__getattr__(name)
          # 상태를 저장하여 동일한 Mock 반환
          mock_obj = MagicMock(return_value=None)
          setattr(self, name, mock_obj)
          return mock_obj
  ```
- **Teardown Design (Duct-Tape Removal)**: `mock_agent_registry` 내부의 `dict`나 `list`를 수동으로 `.clear()` 하는 것은 임시방편(Duct-Tape)입니다. Mock 객체가 GC되지 않고 살아남는 근본 원인(예: Global Registry나 Engine 클래스에 Mock이 캐싱됨)을 추적하여 끊어내야 합니다.
- **Unit Test Teardown Standardization**: `test_monetary_ledger_units.py`에 추가된 `try-finally` 블록의 `ledger.transaction_log.clear()`는 유효하지만, 레저를 테스트하는 모든 코드에 중복 작성될 위험이 있습니다. `MonetaryLedger` 전용 Fixture를 만들어 `yield` 후 초기화하도록 리팩토링하는 것을 권장합니다.

## 5. 🧠 Implementation Insight Evaluation
- **Original Insight**: 
  > "- **Registry Pollution**: The `IAgentRegistry` acts as a hidden SSoT for agent instances. Failure to properly clear and trigger garbage collection on this in `conftest.py` was a primary driver of "State Pollution" and memory leaks in integration scenarios. We enforced strict `reset_mock(return_value=True, side_effect=True)` and `gc.collect(2)` in `clean_room_teardown` to resolve this."
  > "- **Placeholder Vulnerability**: Mocking external libraries (like `numpy`) at the top-level `conftest.py` was a "Duct-Tape" fix that introduced memory instability because simple `MagicMock()`s generate infinite trees on arbitrary attribute access..."
- **Reviewer Evaluation**: 
  Jules가 작성한 이 인사이트는 테스트 환경 내 메모리 누수의 두 가지 주요 패턴(Mock 객체의 무한 증식, 레지스트리에 의한 상태 오염)을 매우 정확하게 진단하고 있습니다. `weakref.proxy`를 통한 순환 참조 해결책은 훌륭한 접근입니다. 그러나 "Registry Pollution" 문제 해결에 대해 스스로 `gc.collect(2)`와 수동 초기화라는 "임시방편(Duct-Tape)"을 정당화하고 있다는 점은 아쉽습니다. 진정한 SSoT 아키텍처라면 `reset_tick_flow`나 라이프사이클 훅을 통해 레지스트리 참조가 깔끔하게 해제되어야 합니다.

## 6. 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
```markdown
### [TEST-MEM-001] Mock Instance Growth & Registry Global Pollution
- **현상**: 대규모 트랜잭션 테스트 혹은 파라미터화된 테스트 수행 시, `MemoryError` 발생 및 `MagicMock` 객체가 테스트당 수백 개씩 누적됨.
- **원인**: 
  1. `numpy` 등 미설치 라이브러리를 단순 `MagicMock()`으로 패치할 경우, 내부 연산에서 Mock Tree가 무한 증식함.
  2. `FinanceSystem`과 `Government` 간의 `self.finance_system.government = self`와 같은 강한 순환 참조.
  3. `IAgentRegistry` Mock이 글로벌하게 참조되어, 함수 스코프 픽스처임에도 GC되지 않고 상태(Transaction Log 등)를 쥐고 있음.
- **해결**: `weakref.proxy`를 도입하여 순환 참조를 끊고, Mock Tree 증식을 막기 위한 `ShallowModuleMock` 도입.
- **교훈**: 테스트 환경에서의 상태 초기화 실패는 단순 에러가 아니라 아키텍처의 결합도가 너무 높음을 알리는 신호다. 강한 순환 참조는 `weakref` 혹은 의존성 주입(DI) 구조 변경으로 해결하고, Fixture의 생명 주기를 글로벌 레지스트리의 라이프사이클과 일치시켜야 한다.
```

## 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**
- **사유 (Vibe Check Fail)**: `ShallowModuleMock`에서 속성 접근 시마다 매번 새로운 객체를 반환하는 로직은 객체 동일성 검증을 훼손하는 잠재적 로직 오류(Logic Bug)를 내포하고 있습니다. 또한, `conftest.py`에서 `mock_agent_registry.agents.clear()`를 `hasattr`로 확인하여 강제로 비우는 방식은 객체 누수의 근본 원인을 고친 것이 아닌 명백한 'Duct-Tape Debugging'입니다. 이를 개선해야 합니다.