# Spec: Macro-Linked Portfolio Decisions (Phase 26 Step 1)

## 1. 개요 (Overview)
가계(Household)의 투자가 단순 기대 수익률(Merton Model)에만 의존하지 않고, **거시 경제 신호(Macro Signals)**에 따라 위험 회피 성향(Risk Aversion)을 동적으로 조절하도록 로직을 확장합니다.

- **목표**: 고인플레이션 또는 경기 침체(GDP 역성장) 시그널이 감지되면, 가계가 주식 비중을 줄이고 안전 자산(예금/현금) 비중을 늘리는 'Flight to Quality' 현상 구현.
- **핵심 변경**: `PortfolioManager`에 `calculate_effective_risk_aversion` 로직 추가.

## 2. 데이터 구조 (Data Structure)

### 2.1 Input: MacroFinancialContext (DTO)
거시 경제 상황을 요약하여 의사결정 모듈에 전달하는 객체입니다.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `inflation_rate` | `float` | 최근 물가 상승률 (SMA) | `SensoryModule` (Gov) |
| `gdp_growth_rate` | `float` | 최근 GDP 성장률 (SMA) | `SensoryModule` (Gov) |
| `market_volatility` | `float` | 주식 시장 변동성 (VIX proxy) | `StockMarketTracker` |
| `interest_rate_trend` | `float` | 금리 변화율 (Delta) | `Bank` |

### 2.2 Output: Dynamic Risk Modifier
기존 `risk_aversion`($\lambda$)에 곱해질 계수입니다.
- **Base State**: 1.0 (변화 없음)
- **Panic State**: > 1.0 (위험 회피 증가)

## 3. 알고리즘 및 로직 (Logic & Algorithms)

### 3.1 동적 위험 회피 계수 산출 (Dynamic Risk Aversion Calculation)

가계의 최종 위험 회피도 $\lambda_{effective}$는 다음과 같이 계산됩니다.

$$ \lambda_{effective} = \lambda_{base} \times (1.0 + \text{Stress}_{inflation} + \text{Stress}_{recession}) $$

#### 의사코드 (Pseudo-code)

```python
def calculate_effective_risk_aversion(base_lambda: float, context: MacroFinancialContext) -> float:
    # 1. 인플레이션 스트레스 (Target 2% 초과 시 공포 증가)
    CONST_INFLATION_TARGET = 0.02
    inflation_excess = max(0.0, context.inflation_rate - CONST_INFLATION_TARGET)
    stress_inflation = inflation_excess * 10.0  # 민감도 가중치 (Tuning 필요)

    # 2. 경기 침체 스트레스 (역성장 시 공포 급증)
    stress_recession = 0.0
    if context.gdp_growth_rate < 0.0:
        stress_recession = abs(context.gdp_growth_rate) * 5.0 # 민감도 가중치

    # 3. 금리 변동성 (옵션)
    # 금리가 급격히 오르면 채권/주식 모두 악재 -> 현금 선호
    stress_rate = max(0.0, context.interest_rate_trend) * 2.0

    total_stress_multiplier = 1.0 + stress_inflation + stress_recession + stress_rate

    # 상한선(Cap) 적용 (너무 극단적인 회피 방지, 예: 최대 3배)
    total_stress_multiplier = min(3.0, total_stress_multiplier)

    return base_lambda * total_stress_multiplier
```

### 3.2 포트폴리오 최적화 파이프라인 수정
기존 `optimize_portfolio` 호출 직전에 위 로직을 수행합니다.

1. `Engine`에서 `MacroFinancialContext` 생성 (Tracker 데이터 기반).
2. `Household.make_decision` 내부에서 `PortfolioManager.calculate_effective_risk_aversion` 호출.
3. 보정된 $\lambda$를 사용하여 `PortfolioManager.optimize_portfolio` 실행.

## 4. 예외 처리 (Exception Handling)
- **데이터 누락**: 시뮬레이션 초기(Tick < 10)에는 SMA 데이터가 불충분할 수 있음. → `context` 값이 0.0이라고 가정하고 Multiplier 1.0 반환 (Fallback).
- **Extreme Value**: 인플레이션이 1000% 등 비정상 수치일 경우 → Multiplier를 Hard Cap(3.0)으로 제한하여 로직 붕괴 방지.

## 5. 검증 계획 (Verification Plan)
- **Test Case 1 (Normal)**: 인플레이션 2%, GDP 성장 3% → Multiplier 1.0 근사 확인.
- **Test Case 2 (Stagflation)**: 인플레이션 10%, GDP 성장 -2% → Multiplier 대폭 상승 확인 (> 1.5).
- **Simulation**: 'Chaos Injection' (Tick 200, 600) 발생 시 가계들의 주식 매도세(Safety Preference)가 관측되어야 함.

---

### [Mandatory Reporting]
**Jules Checkpoint**:
구현 중 발견되는 다음 항목을 `communications/insights/`에 반드시 보고하십시오:
1. 매크로 민감도(가중치) 설정이 너무 높아 시장 붕괴(Flash Crash)를 유발하지 않는지?
2. `MacroFinancialContext` 데이터를 `Engine`에서 효율적으로 집계하고 있는지 (SoC 위반 여부).
