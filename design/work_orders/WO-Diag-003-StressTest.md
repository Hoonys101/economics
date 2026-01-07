# WO-Diag-003: Operation "Forensics" - Stress Test (Crucible Mode)

## 1. 개요 (Overview)
*   **문제**: 이전 Forensics 실행 결과(0 Deaths)는 `INITIAL_HOUSEHOLD_ASSETS`가 너무 높아(5000.0) 에이전트들이 근로 없이도 장기간 생존했기 때문입니다 ("부자 아빠 효과").
*   **목표**: 초기 자산을 극도로 낮춰(Crucible Mode), 에이전트들을 즉시 생존 위기에 빠뜨리고 사망 원인을 분석합니다.

## 2. 작업 상세 (Implementation Details)

### 2.1 임시 파라미터 조정 (`scripts/operation_forensics.py` 수정)
*   **대상 파일**: `scripts/operation_forensics.py`
*   **지시 사항**:
    *   **목적**: 에이전트의 생산성을 압도하는 소비/갈증 상태를 만들어 인위적 기근을 유도하십시오. (Malthusian Trap)
    *   **오버라이드 리스트**:
        *   `config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 10.0` (극단적 빈곤)
        *   `config.GOVERNMENT_STIMULUS_ENABLED = False` (정부 지원 차단)
        *   `config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 5.0` (평소보다 5배 많이 먹음)
        *   `config.GOODS['basic_food']['utility_effects']['survival'] = 1` (식량의 영양가가 1/10로 감소)
        *   `config.FIRM_PRODUCTIVITY_FACTOR = 1.0` (생산성 급감)
    *   참고: `create_simulation()` 호출 직전에 설정.

### 2.2 시뮬레이션 재실행 및 보고
*   수정된 스크립트로 시뮬레이션을 재실행하십시오. (Tick 수: 100~200 유지)
*   **기대 결과**: 다수의 에이전트 사망 발생.
*   `reports/AUTOPSY_REPORT.md` (또는 `forensic_report.txt`)를 갱신하십시오.

## 3. 검증 계획
1.  `python scripts/operation_forensics.py` 실행.
2.  `reports/forensic_report.txt` 확인.
3.  **성공 기준**: Total Deaths > 0.
