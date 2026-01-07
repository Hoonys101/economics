# WO-Diag-003: Operation "Forensics" - Stress Test (Crucible Mode)

## 1. 개요 (Overview)
*   **문제**: 이전 Forensics 실행 결과(0 Deaths)는 `INITIAL_HOUSEHOLD_ASSETS`가 너무 높아(5000.0) 에이전트들이 근로 없이도 장기간 생존했기 때문입니다 ("부자 아빠 효과").
*   **목표**: 초기 자산을 극도로 낮춰(Crucible Mode), 에이전트들을 즉시 생존 위기에 빠뜨리고 사망 원인을 분석합니다.

## 2. 작업 상세 (Implementation Details)

### 2.1 임시 파라미터 조정 (`scripts/operation_forensics.py` 수정)
*   **대상 파일**: `scripts/operation_forensics.py`
*   **지시 사항**:
    *   `config.py`를 직접 수정하지 말고, 시뮬레이션 초기화 직전에 아래 값들을 런타임에서 오버라이드 하십시오.
    *   **목표값**:
        *   `config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 50.0`
        *   `config.GOVERNMENT_STIMULUS_ENABLED = False` (정부의 무분별한 현금 살포 및 구제 금융이 사망을 막고 있음)
    *   참고: `create_simulation()` 호출 전에 설정.

### 2.2 시뮬레이션 재실행 및 보고
*   수정된 스크립트로 시뮬레이션을 재실행하십시오. (Tick 수: 100~200 유지)
*   **기대 결과**: 다수의 에이전트 사망 발생.
*   `reports/AUTOPSY_REPORT.md` (또는 `forensic_report.txt`)를 갱신하십시오.

## 3. 검증 계획
1.  `python scripts/operation_forensics.py` 실행.
2.  `reports/forensic_report.txt` 확인.
3.  **성공 기준**: Total Deaths > 0.
