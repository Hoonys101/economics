# Gemini CLI Tools Reference for Economic Simulation Project

이 문서는 Gemini CLI 에이전트가 경제 시뮬레이션 프로젝트에서 직접 호출하여 사용할 수 있는 주요 Python 함수들을 API 형태로 정의합니다. 이 문서는 Gemini의 내부 도구 목록을 사용자에게 투명하게 공개하고, 세션 간 작업의 연속성을 보장하기 위해 작성되었습니다.

---

## 1. `run_simulation` (from `main.py`)

시뮬레이션을 실행하고 결과를 저장하는 핵심 함수입니다. 다양한 시뮬레이션 시나리오를 실행하는 데 사용됩니다.

### 목적
경제 시뮬레이션을 초기화하고, 지정된 틱(tick) 수만큼 실행하며, 그 결과를 CSV 파일로 저장합니다. 기업의 생산 목표를 조작하여 특정 실험 시나리오를 실행할 수 있습니다.

### 파라미터

-   **`firm_production_targets`** (Optional[List[Dict[str, float]]]):
    -   **타입**: `List[Dict[str, float]]` 또는 `None`
    -   **설명**: 각 기업의 생산 목표를 지정하는 딕셔너리 리스트입니다. 리스트의 각 딕셔너리는 `{ "item_id": target_quantity }` 형태를 가집니다 (예: `{"food": 500.0}`).
    -   `None`이거나 리스트 길이가 기업 수와 다를 경우, `config.py`에 정의된 기본 생산 목표가 사용됩니다.
    -   **예시**: `[{"food": 500.0}, {"luxury_food": 100.0}, ...]`

-   **`output_filename`** (Optional[str]):
    -   **타입**: `str`
    -   **설명**: 시뮬레이션 결과를 저장할 CSV 파일의 이름입니다.
    -   **기본값**: `"simulation_results.csv"`

### 사용 예시 (Gemini 내부 호출)

```python
# 기본 설정으로 시뮬레이션 실행
run_simulation()

# 특정 파일에 결과 저장
run_simulation(output_filename="my_custom_simulation_results.csv")

# 특정 기업의 생산 목표를 조작하여 시뮬레이션 실행 (예: 첫 10개 기업이 food만 500개 생산)
custom_targets = [{"food": 500.0}] * 10
run_simulation(firm_production_targets=custom_targets, output_filename="food_supply_experiment.csv")
```

---

## 2. `select_logs` (from `log_selector.py`)

시뮬레이션 로그 파일(`simulation_results.csv`)에서 특정 조건에 따라 로그를 필터링하고 출력하는 함수입니다.

### 목적
방대한 시뮬레이션 로그 데이터에서 필요한 정보만을 추출하여 분석 및 디버깅을 용이하게 합니다.

### 파라미터

-   **`filename`** (Optional[str]):
    -   **타입**: `str`
    -   **설명**: 로그 파일의 경로입니다.
    -   **기본값**: `"simulation_results.csv"`

-   **`agent_type`** (Optional[str]):
    -   **타입**: `str` 또는 `None`
    -   **설명**: 필터링할 에이전트의 타입 (예: `"Household"`, `"Firm"`, `"Simulation"`).

-   **`agent_id`** (Optional[int]):
    -   **타입**: `int` 또는 `None`
    -   **설명**: 필터링할 에이전트의 고유 ID.

-   **`method_name`** (Optional[str]):
    -   **타입**: `str` 또는 `None`
    -   **설명**: 필터링할 메서드 이름 또는 로그가 발생한 컨텍스트 (예: `"AIDecision"`, `"BuyAttempt"`).

-   **`tick_start`** (Optional[int]):
    -   **타입**: `int` 또는 `None`
    -   **설명**: 로그를 검색할 시작 틱(tick) 번호 (포함).

-   **`tick_end`** (Optional[int]):
    -   **타입**: `int` 또는 `None`
    -   **설명**: 로그를 검색할 종료 틱(tick) 번호 (포함).

-   **`return_df`** (Optional[bool]):
    -   **타입**: `bool`
    -   **설명**: `True`로 설정하면 필터링된 로그를 Pandas DataFrame 형태로 반환합니다. `False`일 경우 로그를 콘솔에 출력합니다.
    -   **기본값**: `False`

### 사용 예시 (Gemini 내부 호출)

```python
# 모든 로그 출력
select_logs()

# 특정 가계의 로그 출력
select_logs(agent_type="Household", agent_id=0)

# 특정 기업의 특정 메서드 로그 출력 (틱 0-10)
select_logs(agent_type="Firm", agent_id=100, method_name="make_decisions", tick_start=0, tick_end=10)

# 필터링된 로그를 DataFrame으로 반환받기
imitation_logs_df = select_logs(agent_type="Household", method_name="Imitation Debug", return_df=True)
```

---

## 3. `count_filtered_logs` (from `log_selector.py`)

시뮬레이션 로그 파일(`simulation_results.csv`)에서 특정 조건에 맞는 로그의 개수를 세는 함수입니다.

### 목적
특정 유형의 로그가 얼마나 자주 발생하는지 빠르게 파악하여 시뮬레이션 동작을 정량적으로 분석합니다.

### 파라미터

-   **`filename`** (Optional[str]):
    -   **타입**: `str`
    -   **설명**: 로그 파일의 경로입니다.
    -   **기본값**: `"simulation_results.csv"`

-   **`agent_type`** (Optional[str]):
    -   **타입**: `str` 또는 `None`
    -   **설명**: 필터링할 에이전트의 타입.

-   **`agent_id`** (Optional[int]):
    -   **타입**: `int` 또는 `None`
    -   **설명**: 필터링할 에이전트의 고유 ID.

-   **`method_name`** (Optional[str]):
    -   **타입**: `str` 또는 `None`
    -   **설명**: 필터링할 메서드 이름 또는 로그가 발생한 컨텍스트.

-   **`tick_start`** (Optional[int]):
    -   **타입**: `int` 또는 `None`
    -   **설명**: 로그를 검색할 시작 틱(tick) 번호 (포함).

-   **`tick_end`** (Optional[int]):
    -   **타입**: `int` 또는 `None`
    -   **설명**: 로그를 검색할 종료 틱(tick) 번호 (포함).

### 사용 예시 (Gemini 내부 호출)

```python
# 특정 조건에 맞는 로그 개수 세기
count = count_filtered_logs(agent_type="Household", method_name="Imitation Debug")
print(f"Total imitation debug logs: {count}")
```

---

## 4. `analyze_supply_shock_results` (from `analyze_results.py`)

수요-공급 법칙 검증 실험의 결과를 분석하고 보고하는 함수입니다.

### 목적
대조군과 실험군 시뮬레이션 결과를 비교하여 'food' 시장의 가격 및 거래량 변화를 분석하고, 수요-공급 법칙이 모델에서 관찰되는지 검증합니다.

### 파라미터

이 함수는 파라미터를 직접 받지 않고, `results_baseline.csv`와 `results_experiment.csv` 파일을 자동으로 로드하여 분석을 수행합니다.

### 사용 예시 (Gemini 내부 호출)

```python
# 수요-공급 실험 결과 분석 실행
analyze_supply_shock_results()
```

---

## 5. `analyze_simulation_results` (from `analyze_simulation.py`)

시뮬레이션의 주요 경제 지표를 요약하고 CSV 파일로 저장하는 함수입니다.

### 목적
시뮬레이션의 전반적인 경제 상태를 간략하게 파악할 수 있는 핵심 지표들을 추출하여 요약 보고서를 생성합니다.

### 파라미터

-   **`input_csv_path`** (Optional[str]):
    -   **타입**: `str`
    -   **설명**: 분석할 시뮬레이션 결과 CSV 파일의 경로입니다.
    -   **기본값**: `"simulation_results.csv"`

-   **`output_csv_path`** (Optional[str]):
    -   **타입**: `str`
    -   **설명**: 요약된 결과를 저장할 CSV 파일의 경로입니다.
    -   **기본값**: `"summary_results.csv"`

### 사용 예시 (Gemini 내부 호출)

```python
# 기본 시뮬레이션 결과 요약
analyze_simulation_results()

# 특정 시뮬레이션 결과 파일 요약
analyze_simulation_results(input_csv_path="my_custom_simulation_results.csv", output_csv_path="my_custom_summary.csv")
```

---

## 6. `search_log_file` (from `utils/log_searcher.py`)

로그 파일에서 특정 키워드를 포함하는 라인을 검색하는 함수입니다.

### 목적
로그 파일에서 특정 이벤트나 메시지를 빠르게 찾아 디버깅 및 분석에 활용합니다.

### 파라미터

-   **`log_file_path`** (str):
    -   **타입**: `str`
    -   **설명**: 검색할 로그 파일의 경로입니다.

-   **`keywords`** (List[str]):
    -   **타입**: `List[str]`
    -   **설명**: 검색할 키워드 리스트입니다.

### 사용 예시 (Gemini 내부 호출)

```python
# 특정 키워드를 포함하는 로그 검색
search_log_file(log_file_path="simulation_results.csv", keywords=["Error", "Transaction"])
```

---

## 7. `run_supply_shock_experiment` (from `run_experiment.py`)

수요-공급 법칙 검증을 위한 대조군 및 실험군 시뮬레이션을 실행하는 함수입니다.

### 목적
사전에 정의된 시나리오에 따라 시뮬레이션을 실행하여 경제학적 가설을 검증합니다.

### 파라미터

이 함수는 파라미터를 직접 받지 않고, 내부적으로 `main.py`의 `run_simulation` 함수를 호출하여 대조군 및 실험군 시뮬레이션을 실행합니다.

### 사용 예시 (Gemini 내부 호출)

```python
# 수요-공급 충격 실험 실행
run_supply_shock_experiment()
```

---

## 8. 대용량 로그 파일 처리 및 디버깅 전략

시뮬레이션 로그 파일(`simulation_results.csv`)은 시뮬레이션 틱이 증가함에 따라 매우 커질 수 있습니다. `log_selector.py`와 같은 도구는 `pandas`를 사용하여 파일을 읽고 필터링하지만, 파일 전체를 메모리에 로드하거나 특정 `limit` 파라미터 없이 사용하면 성능 문제가 발생할 수 있습니다.

**주의사항:**

-   **`read_file` 도구의 `limit` 및 `offset` 파라미터**: `read_file` 도구는 대용량 텍스트 파일을 읽을 때 `limit` 및 `offset` 파라미터를 지원합니다. 이는 파일의 특정 부분만 읽어 메모리 사용량을 줄이고 처리 속도를 높이는 데 유용합니다.
-   **`log_selector.py`의 `select_logs` 함수**: 이 함수는 `return_df=True` 옵션을 통해 필터링된 결과를 Pandas DataFrame으로 반환할 수 있습니다. 이 경우, `tick_start` 및 `tick_end`와 같은 필터링 파라미터를 적극적으로 활용하여 필요한 데이터 범위만 로드하도록 해야 합니다.
-   **디버깅 시 `print` 문 사용 지양**: 대용량 로그 파일이 생성되는 환경에서 `print` 문을 사용하여 디버깅 정보를 콘솔에 직접 출력하는 것은 바람직하지 않습니다. 이는 콘솔 출력 제한으로 인해 중요한 정보가 누락될 수 있으며, 성능에도 영향을 미칠 수 있습니다. 대신, `Logger` 클래스를 통해 `simulation_results.csv`에 디버그 메시지를 기록하고, `log_selector.py`의 필터링 기능을 활용하여 필요한 로그만 조회하는 것이 효율적입니다.

**권장 디버깅 전략:**

1.  **`Logger` 활용**: `self.logger.log()`를 사용하여 모든 디버그 메시지를 `simulation_results.csv`에 기록합니다.
2.  **`log_selector.py`로 필터링**: `log_selector.py`의 `select_logs` 함수를 사용하여 `agent_type`, `agent_id`, `method_name`, `tick_start`, `tick_end` 등의 파라미터를 조합하여 필요한 로그만 효율적으로 조회합니다.
3.  **작은 틱 범위로 테스트**: 문제가 발생하는 특정 틱 범위(예: 0-10 틱)에 대해서만 로그를 필터링하여 분석하면, 대용량 로그 파일의 부담 없이 빠르게 문제를 파악할 수 있습니다.
4.  **`return_df=True` 활용**: 복잡한 분석이 필요한 경우, `select_logs(return_df=True)`를 사용하여 필터링된 데이터를 Pandas DataFrame으로 받아 추가적인 데이터 분석 작업을 수행할 수 있습니다.
