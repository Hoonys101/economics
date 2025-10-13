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

---

# 프로젝트 리팩토링 체크리스트: 관심사의 분리 (Separation of Concerns)

이 문서는 경제 시뮬레이션 프로젝트의 모듈성, 유지보수성, 테스트 용이성 및 유연성을 향상시키기 위한 리팩토링 계획을 담고 있습니다. 각 리팩토링 항목은 명확한 목적과 구체적인 구현 체크리스트로 구성됩니다.

---

## Phase 1: Immediate Architectural Clean-up and Bug Fixes (높은 영향, 낮은 위험)

### 1.1. `Household.get_desired_wage()` 구현

*   **목적:** `design/code_architecture_and_api.md`에 명시된 버그를 해결하고, 가계의 노동 시장 참여 로직의 일관성을 확보합니다.
*   **대상 파일/클래스:** `simulation/core_agents.py` (Household 클래스)
*   **구현 체크리스트:**
    *   [x] `simulation/core_agents.py` 파일 열기.
    *   [x] `Household` 클래스 내 `get_desired_wage()` 메서드 구현.
        *   [x] `config.BASE_WAGE`와 `self.labor_skill`을 기반으로 희망 임금 계산.
        *   [x] 필요시 `HouseholdDecisionEngine`으로 임금 결정 로직 위임 고려. (가계의 생존 욕구와 자산 수준을 복합적으로 고려하는 로직으로 구현 완료)
    *   [ ] 관련 테스트 코드 업데이트 또는 추가 (필요시).
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 노동 시장 참여 확인).

### 1.2. `EconomicIndicatorTracker` 모듈 분리

*   **목적:** `EconomicIndicatorTracker`의 정의와 로직을 `simulation/engine.py`로부터 분리하여 모듈성을 향상시키고 `Simulation` 클래스의 책임을 줄입니다.
*   **대상 파일/클래스:** `simulation/engine.py`, `simulation/metrics/economic_tracker.py` (신규)
*   **구현 체크리스트:**
    *   [ ] `simulation/metrics/` 디렉토리 생성 (없을 경우).
    *   [ ] `simulation/engine.py`에서 `EconomicIndicatorTracker` 클래스 정의를 `simulation/metrics/economic_tracker.py`로 이동.
    *   [ ] `simulation/metrics/economic_tracker.py`에 필요한 임포트 추가.
    *   [ ] `simulation/engine.py`에서 `EconomicIndicatorTracker` 임포트 경로 업데이트.
    *   [ ] `Simulation` 클래스 초기화 시 `EconomicIndicatorTracker` 인스턴스 생성 방식 확인 및 필요시 수정.
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 지표 추적 기능 확인).

### 1.3. 중앙 집중식 설정 접근 (초기 단계)

*   **목적:** `config` 모듈의 직접적인 전역 임포트를 줄이고, 필요한 설정 값을 의존성 주입 방식으로 전달하여 결합도를 낮추고 테스트 용이성을 높입니다.
*   **대상 파일/클래스:** `simulation/engine.py`, `simulation/firms.py`, `simulation/core_agents.py` 등 `config`를 직접 사용하는 주요 모듈
*   **구현 체크리스트:**
    *   [x] `simulation/engine.py`의 `Simulation` 클래스 생성자에 `config_module` 인자가 이미 전달되고 있는지 확인. (확인 완료)
    *   [x] `simulation/firms.py`의 `Firm` 클래스 생성자에 `config_module` 인자가 이미 전달되고 있는지 확인. (확인 완료)
    *   [x] `simulation/core_agents.py`의 `Household` 클래스 생성자에 `config_module` 인자 추가 및 내부 로직에서 `config` 대신 `self.config_module` 사용. (구현 완료)
    *   [ ] `simulation/decisions/action_proposal.py` 등 `config`를 직접 사용하는 다른 주요 모듈 검토 및 필요시 `config_module` 주입 방식으로 전환.
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 설정 값 정상 적용 확인).

---

## Phase 2: Enhanced Logging System Implementation (중간 영향, 중간 위험)

### 2.1. `ContextualFilter` 구현

*   **목적:** `log_config.json`에 정의된 규칙에 따라 로그 메시지를 유연하게 필터링하는 기능을 구현합니다.
*   **대상 파일/클래스:** `utils/logging_manager.py`
*   **구현 체크리스트:**
    *   [ ] `utils/logging_manager.py` 파일 열기.
    *   [ ] `ContextualFilter` 클래스 내 `filter` 메서드 로직 구현.
        *   [ ] `log_config.json`에서 `filters` 섹션 로드.
        *   [ ] `record.extra`에 포함된 `tick`, `module`, `agent_id`, `tags` 정보를 기반으로 필터링 로직 적용.
        *   [ ] `tick_range`, `modules`, `agent_ids`, `tags` 필터링 조건 구현.
    *   [ ] `log_config.json` 파일에 필터링 규칙 예시 추가 (필요시).
    *   [ ] 관련 테스트 코드 업데이트 또는 추가 (필요시).

### 2.2. `ContextualFilter` 로깅 설정에 통합

*   **목적:** 구현된 `ContextualFilter`를 실제 로깅 핸들러에 적용하여 필터링 기능을 활성화합니다.
*   **대상 파일/클래스:** `utils/logging_manager.py`
*   **구현 체크리스트:**
    *   [ ] `utils/logging_manager.py` 파일 열기.
    *   [ ] `setup_logging` 함수 내에서 `ContextualFilter` 인스턴스 생성.
    *   [ ] 생성된 `ContextualFilter` 인스턴스를 `logging.Handler` (예: `FileHandler`, `StreamHandler`)에 추가.
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 `log_config.json` 필터링 규칙에 따라 로그가 올바르게 필터링되는지 확인).

### 2.3. `extra` 파라미터 사용 표준화

*   **목적:** 모든 `logging` 호출에서 `extra` 파라미터를 일관되고 완전하게 사용하여 로그 메시지에 풍부한 컨텍스트 정보를 제공합니다.
*   **대상 파일/클래스:** `simulation/` 디렉토리 내 모든 Python 파일
*   **구현 체크리스트:**
    *   [ ] `simulation/` 디렉토리 내 모든 Python 파일을 순회하며 `logger.debug`, `logger.info`, `logger.warning`, `logger.error` 호출 검토.
    *   [ ] 각 호출에 `extra` 딕셔너리가 포함되어 있는지 확인.
    *   [ ] `extra` 딕셔너리에 `tick`, `agent_id` (해당하는 경우), `tags` (로그 메시지의 성격을 나타내는 키워드)가 일관되게 포함되어 있는지 확인 및 추가.
    *   [ ] `tags`는 로그 메시지의 유형(예: `['household_decision']`, `['firm_production']`, `['market_match']`, `['error']`)을 명확히 나타내도록 정의.
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 로그 파일에서 `extra` 정보가 올바르게 기록되는지 확인).

---

## Phase 3: Deeper Architectural Refinements (장기적, 높은 영향/위험)

### 3.1. `Simulation`의 책임 분리: 전용 프로세서/관리자 도입

*   **목적:** `Simulation` 클래스의 책임을 순수한 오케스트레이션으로 제한하고, 거래 처리 및 에이전트 생명주기 관리와 같은 세부 로직을 전용 클래스로 분리합니다.
*   **대상 파일/클래스:** `simulation/engine.py`, `simulation/processors/transaction_processor.py` (신규), `simulation/managers/agent_lifecycle_manager.py` (신규)
*   **구현 체크리스트:**
    *   [ ] `simulation/processors/` 및 `simulation/managers/` 디렉토리 생성 (없을 경우).
    *   [ ] `simulation/engine.py`에서 `_process_transactions` 메서드 로직을 `simulation/processors/transaction_processor.py` 내 `TransactionProcessor` 클래스로 이동.
    *   [ ] `simulation/engine.py`에서 `_handle_agent_lifecycle` 메서드 로직을 `simulation/managers/agent_lifecycle_manager.py` 내 `AgentLifecycleManager` 클래스로 이동.
    *   [ ] `Simulation` 클래스 생성자에 `TransactionProcessor` 및 `AgentLifecycleManager` 인스턴스 주입.
    *   [ ] `Simulation.run_tick()` 내에서 해당 프로세서/관리자 메서드 호출로 변경.
    *   [ ] 신규 클래스에 필요한 임포트 및 의존성 주입 처리.
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 거래/생명주기 관리 기능 정상 작동 확인).

### 3.2. AI 모듈 책임 명확화 및 세분화

*   **목적:** `simulation/ai/` 디렉토리 내 각 모듈의 단일 책임 원칙(SRP)을 강화하고, AI 관련 로직의 응집도를 높입니다.
*   **대상 파일/클래스:** `simulation/ai/` 디렉토리 내 모든 Python 파일
*   **구현 체크리스트:**
    *   [ ] `simulation/ai/action_selector.py`: 행동 선택 로직만 담당하는지 확인.
    *   [ ] `simulation/ai/state_builder.py`: 에이전트 상태를 AI 모델 입력 형식으로 변환하는 로직만 담당하는지 확인.
    *   [ ] `simulation/ai/reward_calculator.py`: 행동에 대한 보상을 계산하는 로직만 담당하는지 확인.
    *   [ ] `simulation/ai/model_wrapper.py`: ML 모델의 로드/저장/예측/훈련 인터페이스만 제공하는지 확인.
    *   [ ] 각 모듈 내에서 다른 모듈의 책임을 침범하는 로직이 없는지 검토 및 분리.
    *   [ ] 필요시 새로운 모듈 생성 또는 기존 모듈 재구성.
    *   [ ] 변경 사항 검증 (AI 의사결정 및 학습 기능 정상 작동 확인).

### 3.3. 에이전트 로깅 인터페이스 추상화

*   **목적:** 에이전트가 직접 `logging` 모듈을 호출하는 대신, 추상화된 인터페이스를 통해 로깅을 수행하도록 하여 에이전트 코드의 복잡성을 줄이고 로깅 방식 변경에 대한 유연성을 확보합니다.
*   **대상 파일/클래스:** `simulation/base_agent.py`, `simulation/core_agents.py`, `simulation/firms.py`
*   **구현 체크리스트:**
    *   [ ] `simulation/base_agent.py` 내 `BaseAgent` 클래스에 `_log_agent_action(self, level, message, **kwargs)`와 같은 헬퍼 메서드 추가.
        *   [ ] 이 헬퍼 메서드는 `self.logger`를 사용하여 실제 로깅을 수행하며, `tick`, `agent_id`, `tags`와 같은 공통 `extra` 파라미터를 자동으로 주입.
    *   [ ] `Household` 및 `Firm` 클래스 내에서 `self.logger.debug(..., extra={...})` 형태의 직접적인 로깅 호출을 `self._log_agent_action(...)` 헬퍼 메서드 호출로 대체.
    *   [ ] 변경 사항 검증 (시뮬레이션 실행 및 에이전트 로그 메시지 정상 기록 확인).