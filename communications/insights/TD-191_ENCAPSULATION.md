# Insight: Weak Typing & Encapsulation Violation (TD-191)

- **Date**: 2026-02-03
- **Status**: FIXED
- **Target**: `HousingTransactionHandler`, `Household`

## 1. 현상 (Phenomenon)
- `Any` 타입을 광범위하게 사용하여 런타임에 `AttributeError` 또는 `KeyError`가 발생할 위험이 높았음.
- 시스템 로직(e.g., `HousingTransactionHandler`)이 에이전트(`Household`)의 내부 상태(`_econ_state.owned_properties`)를 직접 조작하여 캡슐화 원칙을 위반함.

## 2. 원인 (Cause)
- 초기 개발 단계에서 빠른 프로토타이핑을 위해 타입 검사를 느슨하게 적용함.
- 객체 간의 책임과 경계가 명확히 정의되지 않아, 외부 객체가 내부 구현에 깊이 의존하게 됨.

## 3. 해결 (Solution)
- `Any`를 구체적인 `Protocol`과 `DTO`로 대체하여 컴파일 타임에 타입 정합성을 검증함. (`FiscalMonitor`, `CrisisMonitor` 등)
- 에이전트에 상태를 변경하는 공개 메서드(`add_property`, `remove_property`)를 추가하고, 외부에서는 이 메서드를 통해서만 상태 변경을 요청하도록 수정 ("Tell, Don't Ask" 원칙 적용).
- 변경 사항을 검증하기 위한 단위 테스트를 추가함.

## 4. 교훈 (Lesson Learned)
- 느슨한 타이핑은 단기적인 개발 속도를 높일 수 있지만, 장기적으로는 시스템의 복잡성과 예측 불가능성을 증가시켜 유지보수 비용을 급격히 상승시킨다.
- 객체의 내부 상태는 반드시 캡슐화되어야 하며, 상태 변경은 명시적인 인터페이스(메서드)를 통해서만 이루어져야 한다.
