# 수요 공급 법칙 검증 문제 해결 (Supply-Demand Law Verification Troubleshooting)

## 1. 문제 인식 (Problem Recognition)
경제 시뮬레이션에서 수요 공급 법칙이 제대로 작동하는지 검증해야 했습니다. 초기에는 `analyze_supply_demand.py` 스크립트와 `run_experiment.py` 스크립트를 활용하여 'food' 상품에 대한 가격 및 거래량 변화를 관찰하고자 했습니다.

## 2. 확인 방법 (Verification Method)
1.  `config.py`를 수정하여 `FOOD_SUPPLY_MODIFIER` 변수를 도입, 식량 공급량을 유연하게 조절할 수 있도록 했습니다.
2.  `run_experiment.py`를 수정하여 기준선(Baseline), 공급 증가(Increased Supply), 공급 감소(Decreased Supply)의 세 가지 시나리오를 실행하고, 각 시나리오의 결과를 데이터베이스에 저장하도록 했습니다.
3.  `run_experiment.py` 내에 `extract_and_save_economic_indicators` 함수를 추가하여 시뮬레이션 종료 후 데이터베이스(`simulation_data.db`)에서 경제 지표(`economic_indicators` 테이블)를 추출, CSV 파일로 저장하도록 했습니다.
4.  `analyze_supply_demand.py`를 수정하여 세 가지 시나리오의 CSV 파일을 모두 읽어 분석하고, 수요 공급 법칙의 만족 여부를 판단하도록 했습니다.

## 3. 발생한 문제 (Issues Encountered)

### 3.1. CSV 파일 누락 오류
*   **오류 메시지**: `Error reading CSV files: [Errno 2] No such file or directory: 'results_experiment_increased.csv'`
*   **원인**: `main.run_simulation` 함수가 `output_filename` 인자를 받지만, 실제로는 시뮬레이션 결과를 CSV 파일로 직접 저장하지 않고 데이터베이스(`simulation_data.db`)에 저장하고 있었습니다. 따라서 `analyze_supply_demand.py`가 필요한 CSV 파일을 찾을 수 없었습니다.
*   **해결**: `run_experiment.py`에 `extract_and_save_economic_indicators` 함수를 추가하여 시뮬레이션 실행 후 데이터베이스에서 필요한 데이터를 추출하여 CSV 파일로 저장하도록 했습니다.

### 3.2. 데이터베이스 컬럼명 불일치 오류 (1차)
*   **오류 메시지**: `Execution failed on sql 'SELECT tick, food_avg_price, food_trade_volume FROM economic_indicators ORDER BY tick': no such column: tick`
*   **원인**: `economic_indicators` 테이블에 `tick`이라는 컬럼이 존재하지 않고, 대신 `time`이라는 컬럼이 존재했습니다.
*   **해결**: `run_experiment.py`의 `extract_and_save_economic_indicators` 함수 내 SQL 쿼리에서 `tick`을 `time`으로 수정했습니다.

### 3.3. 데이터베이스 컬럼명 불일치 오류 (2차)
*   **오류 메시지**: `Execution failed on sql 'SELECT time, food_avg_price, food_trade_volume FROM economic_indicators ORDER BY time': no such column: food_trade_volume`
*   **원인**: `economic_indicators` 테이블에 `food_trade_volume`이라는 컬럼이 존재하지 않고, 대신 `total_food_consumption`이라는 컬럼이 존재했습니다.
*   **해결**: `run_experiment.py`의 `extract_and_save_economic_indicators` 함수 내 SQL 쿼리에서 `food_trade_volume`을 `total_food_consumption`으로 수정했습니다.

## 4. 해결 방법 (Solution Method)
위에서 언급된 각 문제에 대한 해결책을 적용하여 `config.py`, `run_experiment.py`, `analyze_supply_demand.py` 파일을 수정했습니다. 특히 `run_experiment.py`에 데이터 추출 로직을 추가하고, SQL 쿼리의 컬럼명을 데이터베이스 스키마에 맞게 `time`과 `total_food_consumption`으로 변경했습니다.

## 5. 현재 상태 (Current Status)
`run_experiment.py`는 이제 세 가지 시나리오(기준선, 공급 증가, 공급 감소)를 실행하고, 각 시나리오의 경제 지표를 `simulation_data.db`에서 추출하여 올바른 CSV 파일(`results_baseline.csv`, `results_experiment_increased.csv`, `results_experiment_decreased.csv`)로 저장할 준비가 되었습니다. 다음 단계는 `analyze_supply_demand.py`를 수정하여 `total_food_consumption` 컬럼을 사용하도록 한 후, 전체 실험을 다시 실행하고 분석하는 것입니다.
