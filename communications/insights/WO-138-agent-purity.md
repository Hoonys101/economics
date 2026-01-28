# Insight Report: Agent Purity and Dependency Injection

- **Mission Key**: WO-138
- **Author**: Jules
- **Date**: 2026-01-28

## 현상 (Phenomenon)

에이전트(`Household`, `Firm`) 및 하위 모듈 코드에 `Bank`, `Government` 등 핵심 커널 객체에 대한 직접적인 참조 및 임포트가 산재하여 결합도가 높았음. 이로 인해 유닛 테스트가 어렵고, 객체 교체가 불가능하며, 아키텍처 경계가 무너지는 문제가 발생.

## 원인 (Cause)

에이전트가 정부의 ID와 같은 특정 정보를 얻기 위해 전역 `config`를 임포트하거나, 커널 객체의 타입을 직접 참조하는 설계 때문. 명확한 의존성 주입 메커니즘의 부재.

## 해결 (Solution)

1.  **Purity Gate 도입**: `pyproject.toml`에 금지된 임포트/타입을 정의하는 `[tool.purity]` 규칙을 추가하고, 이를 CI/CD 단계에서 검사하는 `scripts/verify_purity.py` 스크립트를 구현.
2.  **의존성 주입 (Dependency Injection)**: 오케스트레이션 레이어(`Phase1_Decision`)에서 에이전트에게 필요한 커널 객체 ID들을 `agent_registry` 딕셔너리로 만들어 `DecisionContext`를 통해 주입.
3.  **결과**: 에이전트는 더 이상 커널의 구체적인 구현 클래스를 알 필요 없이, `Context`를 통해서만 외부 세계와 상호작용하게 됨.

## 교훈 (Lesson Learned)

에이전트를 '순수 행위자(Pure Agent)'로 설계해야 한다. 에이전트의 의사결정은 오직 주입된 `Context`에만 의존해야 하며, 외부 상태(전역 config, 싱글톤 객체)를 직접 참조해서는 안 된다. 이는 테스트 용이성을 극대화하고 시스템의 모듈성을 강화하는 핵심 아키텍처 원칙이다.
