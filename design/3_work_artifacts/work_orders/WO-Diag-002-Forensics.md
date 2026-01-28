# WO-Diag-002: Operation "Forensics" Implementation

## 1. 개요 (Overview)
*   **목표**: 에이전트 사망 원인(Type A/B/C)을 규명하기 위한 정밀 로깅 및 보고서 생성 시스템 구현.
*   **참조**: `design/specs/diagnosis_autopsy_spec.md` (Design Spec)

## 2. 작업 상세 (Implementation Details)

### 2.1 로그 시스템 구현 (`simulation/systems/diagnostics.py` 신설 추천)
*   **파일 생성**: `simulation/systems/diagnostics.py`
    *   `DeathRegistry` 클래스 구현 (Singleton 또는 Static).
    *   `record_death(agent, market_context)` 메서드 구현.

### 2.2 Agent 사망 로직 수정
*   **대상 파일**: `simulation/core_agents.py` (Household)
*   **변경 사항**:
    *   `die()` 메서드 내에서 `DeathRegistry.record_death()` 호출.
    *   사망 직전의 상태(자산, Needs, 마지막 오퍼 시간 등)를 캡처하여 전달.

### 2.3 리포트 생성기 구현
*   **대상 파일**: `scripts/analyze_deaths.py` (신규) 또는 `simulation/systems/diagnostics.py` 내 기능 추가.
*   **기능**:
    *   수집된 사망 로그를 분석하여 Type A(구조적), B(매칭), C(소비)로 분류.
    *   `reports/AUTOPSY_REPORT.md` 파일 생성.

## 3. 실행 및 검증 (Execution & Verification)
1.  **시뮬레이션 실행**: 기존 `iron_test.py`를 사용하여 100~200틱 실행 (사망자 발생 유도).
    ```bash
    python scripts/iron_test.py --num_ticks 200
    ```
2.  **리포트 생성**:
    *   시뮬레이션 종료 시 자동으로 생성되거나, 별도 스크립트 실행.
3.  **결과 확인**:
    *   `reports/AUTOPSY_REPORT.md`가 생성되었는지 확인.
    *   내용에 "Type A", "Type B", "Type C" 분류 통계가 포함되어 있는지 확인.
