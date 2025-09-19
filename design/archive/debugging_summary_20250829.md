# 디버깅 요약 및 향후 계획 (2025-08-29)

## 1. 현재까지 확인된 내용 (Confirmed Findings)

- **중앙 집중식 로깅 시스템 구현 완료:**
    - `utils/logging_manager.py` 모듈을 통해 `log_config.json` 기반의 유연한 로깅 시스템이 구축되었습니다.
    - `main.py`, `simulation/engine.py`, `simulation/decisions/firm_decision_engine.py`, `simulation/decisions/household_decision_engine.py`, `simulation/markets.py`, `simulation/loan_market.py`, `simulation/agents/bank.py`, `simulation/core_agents.py`, `simulation/firms.py`, `simulation/ai_model.py` 등 주요 모듈에 새로운 로깅 시스템이 적용되었습니다.
    - `Tick` 및 `Agent ID` 등 컨텍스트 정보가 로그에 포함되며, `log_config.json`의 필터링 규칙에 따라 로그가 정상적으로 기록됨을 확인했습니다.

- **기존 오류 해결:**
    - `ImportError`, `AttributeError` (로거 관련), `KeyError` (로거 포맷 관련) 등 초기 로깅 시스템 구현 과정에서 발생했던 대부분의 오류가 해결되었습니다.
    - `Bank` 객체에 `value_orientation` 및 `needs` 속성을 더미로 추가하여 `ai_trainer`가 `Bank` 객체를 처리하려 할 때 발생하던 `AttributeError`를 일시적으로 해결했습니다.

## 2. 현재 직면한 문제 (Current Blocking Issue)

- **`TypeError: unhashable type: 'dict'` 오류 재발:**
    - **원인:** `simulation/engine.py`의 `run_tick` 함수 내 `agent_pre_tick_states`를 생성하는 과정에서 발생합니다.
    - `agent_pre_tick_states = {agent.id: self.ai_trainer.get_engine(agent.value_orientation)._get_agent_state(agent) for agent in self.get_all_agents()}`
    - `get_all_agents()` 함수는 `value_orientation` 속성을 가진 에이전트만 반환하도록 수정되었으나, `Bank` 객체에 더미 `value_orientation`을 추가하면서 `Bank` 객체도 이 필터링을 통과하게 되었습니다.
    - 결과적으로 `Bank` 객체가 `ai_trainer.get_engine()`으로 전달되고, `Bank` 객체는 AI 훈련 대상이 아니므로 `_get_agent_state` 함수가 `Bank` 객체를 처리할 수 없어 `unhashable type: 'dict'` 오류가 발생합니다.

## 3. 디버깅 단계 및 해결 시도 (Debugging Steps & Attempts)

1.  **`logging_manager.py` 개선:** `LogRecordFactory` 및 `ContextualFilter`를 개선하여 `extra` 인자가 누락된 로그에도 기본값을 제공하도록 수정했습니다.
2.  **`Bank` 객체 속성 추가:** `Bank` 객체에 `value_orientation = "N/A"` 및 `needs = {}`를 추가하여 `AttributeError`를 해결했습니다.
3.  **`engine.py`의 `get_all_agents` 필터링 강화:** `value_orientation` 속성이 있는 에이전트만 반환하도록 수정했습니다. (하지만 `Bank`에 더미 속성을 추가하면서 이 필터링이 무력화됨)
4.  **`ai_model.py`의 `AITrainingManager.end_episode` 필터링 강화:** `value_orientation != "N/A"` 조건을 추가하여 `Bank` 객체를 명시적으로 제외하도록 수정했습니다.
5.  **현재 해결 시도:** `simulation/engine.py`의 `run_tick` 함수 내 `agent_pre_tick_states` 생성 라인에서 `value_orientation`이 "N/A"인 에이전트를 직접 제외하도록 수동 수정을 요청했습니다.

## 4. 향후 계획 (Next Steps)

1.  **사용자 수동 수정 검증:** 사용자가 `simulation/engine.py`의 `agent_pre_tick_states` 생성 라인을 수동으로 수정한 후, 시뮬레이션을 실행하여 `unhashable type: 'dict'` 오류가 해결되었는지 검증합니다.
2.  **로깅 시스템 확장 지속:** 오류 해결 후, `design/TODO_logging_system.md`에 따라 아직 로깅 시스템이 적용되지 않은 다른 모듈들(`simulation/base_agent.py`, `simulation/models.py` 등)에 로깅을 점진적으로 적용합니다.
3.  **기존 `print`문 제거:** 모든 로깅 전환이 완료되면, 프로젝트 내에 남아있는 불필요한 `print`문을 제거합니다.

---