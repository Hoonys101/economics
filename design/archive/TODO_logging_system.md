# 신규 로깅 시스템 구현 TODO 리스트

## Phase 1: 기본 골격 구현

- [x] **1. (문서화)** 신규 로깅 시스템 설계안 작성 (`중앙_집중식_로깅_시스템_설계.md`)
- [x] **2. (파일 생성)** `log_config.json` 설정 파일을 프로젝트 루트에 생성
- [x] **3. (모듈 생성)** `utils/logging_manager.py` 파일 생성
- [x] **4. (구현)** `logging_manager.py`에 `setup_logging` 함수와 `ContextualFilter` 클래스의 기본 골격 구현
- [x] **5. (연동)** `main.py` (또는 `run_experiment.py`) 시작 지점에 `setup_logging()` 호출 코드 추가

## Phase 2: 핵심 모듈 전환 및 검증

- [x] **1. (전환)** `simulation/engine.py`의 기존 로그/print문을 신규 로깅 시스템으로 전환
- [x] **2. (전환)** `simulation/decisions/firm_decision_engine.py`의 기존 로그/print문을 신규 로깅 시스템으로 전환
- [x] **3. (검증)** 시뮬레이션을 실행하고, `log_config.json`의 필터 규칙(`tick_range`, `modules` 등)에 따라 `logs/debug_custom.log` 파일에 로그가 선택적으로 기록되는지 확인

## Phase 3: 확장 및 안정화

- [ ] **1. (확장)** 다른 주요 모듈들(`household_decision_engine` 등)에 신규 로깅 시스템 점진적 적용
- [ ] **2. (정리)** 프로젝트 내 불필요한 `print`문 전체 제거
- [ ] **3. (개선)** `output: console` 모드 및 기타 편의 기능 추가 고려