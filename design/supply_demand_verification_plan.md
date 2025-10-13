# 수요-공급 법칙 검증 계획 (Supply-Demand Law Verification Plan)

## 1. 목표

경제 시뮬레이션 모델이 기본적인 경제학 원리인 수요-공급 법칙을 따르는지 검증합니다. 특히, 'food' 재화의 공급량을 인위적으로 늘렸을 때 시장 가격이 하락하고 거래량이 증가하는지 확인합니다.

## 2. 실험 설정

### 2.1. 실험 변수

*   **독립 변수:** 'food' 재화의 공급량
*   **종속 변수:** 'food' 재화의 평균 시장 가격 (`food_avg_price`), 'food' 재화의 총 거래량 (`food_trade_volume`)

### 2.2. 실험 조건

*   **Baseline Run (기본 실행):**
    *   `config.ENABLE_FOOD_SUPPLY_EXPERIMENT = False`
    *   'food' 재화는 일반적인 생산 로직에 따라 공급됩니다.
    *   결과 파일: `results_baseline.csv`

*   **Experiment Run (실험 실행 - 공급량 증가):**
    *   `config.ENABLE_FOOD_SUPPLY_EXPERIMENT = True`
    *   `config.FOOD_SUPPLY_INCREASE_AMOUNT`에 설정된 값만큼 'food' 재화의 생산량이 인위적으로 증가합니다.
    *   결과 파일: `results_experiment.csv`

## 3. 실행 방법

### 3.1. 시뮬레이션 실행

두 가지 실험 조건(Baseline 및 Experiment)에 따라 시뮬레이션을 실행하고 데이터를 생성합니다.

```bash
python run_experiment.py
```

*   이 스크립트는 `config.ENABLE_FOOD_SUPPLY_EXPERIMENT` 값을 자동으로 변경하며 `results_baseline.csv`와 `results_experiment.csv` 파일을 생성합니다.

### 3.2. 결과 분석

생성된 CSV 파일을 사용하여 수요-공급 법칙의 검증 결과를 분석합니다.

```bash
python analyze_supply_demand.py
```

*   이 스크립트는 두 CSV 파일에서 'food'의 평균 가격과 거래량을 비교하고, 수요-공급 법칙에 부합하는지 여부에 대한 관찰 및 결론을 출력합니다.

## 4. 예상 결과

*   **가격:** Experiment Run (`results_experiment.csv`)의 'food_avg_price'는 Baseline Run (`results_baseline.csv`)보다 낮게 나타나야 합니다.
*   **거래량:** Experiment Run (`results_experiment.csv`)의 'food_trade_volume'은 Baseline Run (`results_baseline.csv`)보다 높게 나타나야 합니다.

이러한 결과가 관찰된다면, 시뮬레이션 모델이 수요-공급 법칙을 성공적으로 반영하고 있음을 의미합니다.

## 5. 다음 단계

수요-공급 법칙이 성공적으로 검증되면, 다음 우선순위 과제인 **[P2 - Major] UI 성능 개선 및 정확성 확보** 또는 **[P2 - Major] 핵심 로직 단위/통합 테스트 작성**으로 진행합니다. (MASTER_PLAN.md 참조)