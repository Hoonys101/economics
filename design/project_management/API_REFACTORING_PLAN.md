# API 리팩토링 및 정리 계획

## 1. 목표
- 코드 가독성 향상: 타입 힌트(Type Hint)를 적극적으로 사용하여 코드의 의도를 명확히 하고 이해도를 높입니다.
- 외부 사용 용이성 증대: 각 모듈 및 객체의 API를 명확히 정의하여 외부에서 코드를 사용할 때 필요한 참조를 최소화하고, 사용 방법을 직관적으로 파악할 수 있도록 합니다.
- 오류 파악 용이성: 명확한 API 정의와 타입 힌트를 통해 개발 단계에서 오류를 조기에 발견하고, 디버깅 시간을 단축합니다.

## 2. 계획 상세

### 2.1. 범위 이해 및 핵심 모듈 식별
- `simulation` 디렉토리 내의 모든 Python 파일을 대상으로 합니다.
- 특히 `simulation/core_markets.py`, `simulation/firms.py`, `simulation/core_agents.py`, `simulation/engine.py`, `simulation/decisions` 등 핵심 로직을 포함하는 모듈을 우선적으로 검토합니다.
- 각 모듈에서 외부로 노출되는 클래스, 함수, 메서드를 API 대상으로 식별합니다.

### 2.2. API 표준 정의
- **타입 힌트:** 모든 함수/메서드의 매개변수 및 반환 값에 타입 힌트를 추가합니다. 클래스 속성에도 필요시 타입 힌트를 적용합니다.
- **독스트링(Docstring):** 모든 공개(Public) 클래스, 함수, 메서드에 명확하고 간결한 독스트링을 추가합니다. 독스트링에는 다음 내용이 포함되어야 합니다:
    - 기능 요약
    - 매개변수(Parameters): 이름, 타입, 설명
    - 반환 값(Returns): 타입, 설명
    - 예외(Raises): 발생 가능한 예외 및 설명 (필요시)
- **API 명확화:**
    - 모듈 간의 의존성을 최소화하고, 각 모듈이 단일 책임을 가지도록 설계합니다.
    - 불필요하게 외부에 노출되는 내부 메서드나 속성은 `_` 접두사를 사용하여 비공개(Private)임을 명시합니다.
    - `simulation/api.py` 파일을 생성하여 주요 모듈의 핵심 API를 한눈에 볼 수 있도록 정리합니다. (예: `from .core_markets import Market`과 같이 재익스포트)

### 2.3. 모듈 우선순위 지정
- **Tier 1 (높음):** `simulation/core_markets.py`, `simulation/core_agents.py`, `simulation/firms.py`, `simulation/engine.py`
    - 시뮬레이션의 핵심 구성 요소로, 이들의 API가 명확해야 다른 모듈 작업이 용이합니다.
- **Tier 2 (중간):** `simulation/decisions` 디렉토리 내의 파일들, `simulation/ai_model.py`
    - 에이전트의 의사결정 로직 및 AI 모델 관련 부분입니다.
- **Tier 3 (낮음):** 그 외 유틸리티성 모듈 및 보조 파일들

### 2.4. 변경 사항 구현
- 각 우선순위에 따라 모듈별로 타입 힌트 및 독스트링을 추가하고 API를 명확히 합니다.
- `simulation/api.py` 파일에 핵심 API들을 재익스포트하여 중앙 집중식 접근점을 제공합니다.

### 2.5. 검증
- **정적 분석:** `ruff`와 같은 린터(Linter)를 사용하여 타입 힌트 및 코드 스타일 가이드라인 준수 여부를 확인합니다.
- **단위 테스트:** 기존 단위 테스트가 변경 사항으로 인해 실패하지 않는지 확인하고, 필요시 테스트 코드를 업데이트합니다.
- **통합 테스트:** 시뮬레이션 전체를 실행하여 변경 사항이 시스템의 전반적인 동작에 부정적인 영향을 미치지 않는지 확인합니다.

## 3. `simulation/api.py` 파일 관리 방안
- 이 파일은 각 모듈의 핵심 클래스나 함수를 재익스포트하는 역할을 합니다.
- 예시:
    ```python
    # simulation/api.py
    from .core_markets import Market, OrderBookMarket
    from .core_agents import Household, Firm
    from .engine import SimulationEngine
    # ... 기타 핵심 API들
    ```
- 이 파일을 통해 외부에서 `from simulation.api import Market, Household` 와 같이 간결하게 핵심 객체에 접근할 수 있도록 합니다.
- 리팩토링 진행 상황에 맞춰 이 파일을 지속적으로 업데이트합니다.
