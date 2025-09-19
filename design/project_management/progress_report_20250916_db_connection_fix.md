# 진행 보고서: DB 연결 오류 수정 및 시뮬레이션 데이터 지속성 안정화 (2025년 9월 16일)

## 1. 문제 분석 및 해결

### 1.1. 문제 인식
백그라운드 시뮬레이션 스레드와 Flask API 엔드포인트 모두에서 `sqlite3.ProgrammingError: Cannot operate on a closed database.` 오류가 반복적으로 발생했습니다. 이는 시뮬레이션 충돌 및 UI의 거래 내역 표시 실패로 이어졌습니다.

### 1.2. 근본 원인
데이터베이스 연결 관리 방식의 문제였습니다. Flask의 `teardown_appcontext`는 웹 요청에 대한 데이터베이스 연결을 관리하고 요청이 끝나면 연결을 닫습니다. 그러나 시뮬레이션 루프는 별도의 스레드에서 실행되며, 이 스레드가 닫힌 데이터베이스 연결을 사용하려고 시도하면서 오류가 발생했습니다.

### 1.3. 해결책 (app.py 수정)
`app.py`의 `run_simulation_loop` 함수를 수정하여 시뮬레이션 스레드 전용의 `SimulationRepository` 인스턴스를 생성하고 관리하도록 변경했습니다. 이 `simulation_repo`는 Flask의 요청 컨텍스트와 독립적으로 동작하며, 시뮬레이션 스레드의 수명 주기 동안 연결이 유지되고 스레드 종료 시 안전하게 닫히도록 `try...finally` 블록 내에서 관리됩니다.

## 2. 현재 진행 상황 및 다음 단계

### 2.1. `app.py` 수정 완료
`app.py` 파일의 `run_simulation_loop` 함수에 대한 수정은 성공적으로 적용되었습니다. 이제 시뮬레이션 스레드는 자체적인 데이터베이스 연결을 사용합니다.

### 2.2. 다음 단계: `simulation/engine.py` 수정
다음으로 `simulation/engine.py` 파일을 수정해야 합니다. `Simulation` 클래스의 `__init__` 메서드와 `run_tick` 메서드가 `app.py`에서 전달되는 전용 `SimulationRepository` 인스턴스를 받아 사용하도록 변경해야 합니다.

### 2.3. 도구 사용의 어려움
`replace` 및 `edit_block`과 같은 직접적인 문자열 교체 도구 사용에 반복적인 어려움이 있었습니다. 이는 정확한 문자열 일치 문제로 인해 발생했으며, 앞으로는 필요한 경우 파일 전체를 읽고 메모리에서 수정한 후 다시 쓰는 방식을 고려할 것입니다.

## 3. 향후 계획

1.  **`simulation/engine.py` 수정:** `Simulation` 클래스 내에서 `self.repository`를 사용하는 모든 부분을 `run_tick` 메서드로 전달된 `repository` 인스턴스를 사용하도록 변경합니다.
2.  **`simulation/db/repository.py` 검토:** `SimulationRepository` 클래스 자체의 연결 관리 로직이 다양한 사용 시나리오(전용 스레드, Flask 요청)에 대해 견고한지 최종 검토합니다.
3.  **테스트 및 검증:** Flask 서버를 재시작하고 시뮬레이션을 실행하여 `Cannot operate on a closed database` 오류가 완전히 해결되었는지 확인합니다. UI의 거래 내역 표시가 정상적으로 작동하는지 검증합니다.

이 보고서는 현재까지의 진행 상황을 요약하며, 다음 작업에 대한 명확한 방향을 제시합니다.