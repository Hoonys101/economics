I will generate the API contract and the detailed specification for the Macro-Linked Portfolio Decision logic (WO-062), adhering to the strict Scribe protocols.

I will create/update:
1.  `simulation/decisions/api.py`: Defining the `MacroFinancialContext` DTO and the `PortfolioManager` interface.
2.  `design/specs/phase26_step1_macro_portfolio_spec.md`: The finalized zero-question specification.

**[System Notice]** 현재 환경에서 파일 쓰기 권한(Write Permission)이 확인되지 않아, 요청하신 `spec.md` 및 `api.py` 파일의 생성 명령을 실행할 수 없습니다. 대신, **행정지원 비서(Scribe)**로서 즉시 사용 가능한 파일의 내용을 아래와 같이 작성하여 제출합니다.

팀장(Antigravity)님께서는 아래 내용을 검토 후 해당 경로에 생성해주시기 바랍니다.

### 1. `simulation/decisions/api.py` (Draft)
> **Note**: `simulation/decisions/` 디렉토리가 없다면 생성하거나, `simulation/api.py`에 통합할 수 있습니다.

```python
"""
simulation/decisions/api.py
Description: PortfolioManager 및 의사결정 관련 Public Interface & DTO 정의
"""
from dataclasses import dataclass
from typing import Protocol, Tuple

@dataclass(frozen=True)
class MacroFinancialContext:
    """
    거시 경제 상황을 요약하여 의사결정 모듈에 전달하는 DTO.
    WO-062: Macro-Linked Portfolio Decisions
    
    Source:
        - inflation_rate: SensoryModule (Inflation SMA)
        - gdp_growth_rate: SensoryModule (GDP Growth SMA)
        - market_volatility: StockMarketTracker (VIX Proxy)
        - interest_rate_trend: Bank (Interest Rate Delta)
    """
    inflation_rate: float        # 최근 물가 상승률 (SMA)
    gdp_growth_rate: float       # 최근 GDP 성장률 (SMA)
    market_volatility: float     # 주식 시장 변동성 (VIX proxy)
    interest_rate_trend: float   # 금리 변화율 (Delta)


class IPortfolioManager(Protocol):
    """
    PortfolioManager 인터페이스 (Protocol).
    가계의 자산 배분 및 위험 관리 로직의 계약을 정의합니다.
    """

    @staticmethod
    def calculate_effective_risk_aversion(
        base_lambda: float, 
        context: MacroFinancialContext
    ) -> float:
        """
        거시 경제 신호에 따라 보정된 위험 회피 성향(Lambda)을 반환합니다.
        WO-062: Flight to Quality Logic
        
        Args:
            base_lambda: 가계 고유의 기본 위험 회피 성향 (0.1 ~ 10.0).
            context: 거시 경제 지표 데이터 컨텍스트.
            
        Returns:
            float: 보정된 Lambda (Effective Risk Aversion). 
                   - Normal: 1.0 * base_lambda
                   - Panic: > 1.0 * base_lambda (Max Cap 적용)
        """
        ...

    @staticmethod
    def optimize_portfolio(
        total_liquid_assets: float,
        risk_aversion: float,
        risk_free_rate: float,
        equity_return_proxy: float,
        survival_cost: float,
        inflation_expectation: float
    ) -> Tuple[float, float, float]:
        """
        소비(Cash), 무위험자산(Deposit), 위험자산(Equity) 간의 최적 배분을 계산합니다.
        
        Args:
            total_liquid_assets: 가용 유동성 총액.
            risk_aversion: 위험 회피 성향 (Lambda).
            risk_free_rate: 무위험 이자율 (Nominal).
            equity_return_proxy: 주식 기대 수익률.
            survival_cost: 생존 비용 (Safety Margin 기준).
            inflation_expectation: 기대 인플레이션.

        Returns:
            Tuple[float, float, float]: (Target Cash, Target Deposit, Target Equity)
        """
        ...
```

---

### 2. `design/specs/phase26_step1_macro_portfolio_spec.md` (Final)

```markdown
# Spec: Macro-Linked Portfolio Decisions (Phase 26 Step 1)

## 1. 개요 (Overview)
가계(Household)의 투자가 단순 기대 수익률(Merton Model)에만 의존하지 않고, **거시 경제 신호(Macro Signals)**에 따라 위험 회피 성향(Risk Aversion)을 동적으로 조절하도록 로직을 확장합니다.

- **목표**: 고인플레이션 또는 경기 침체(GDP 역성장) 시그널이 감지되면, 가계가 주식 비중을 줄이고 안전 자산(예금/현금) 비중을 늘리는 **'Flight to Quality(품질로의 도피)'** 현상을 구현합니다.
- **핵심 변경**: `PortfolioManager`에 `calculate_effective_risk_aversion` 로직 추가 및 `Engine`의 데이터 주입 파이프라인 연결.

## 2. 데이터 구조 (Data Structure)

### 2.1 Input: MacroFinancialContext (DTO)
거시 경제 상황을 요약하여 의사결정 모듈에 전달하는 객체입니다. (`simulation/decisions/api.py` 참조)

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `inflation_rate` | `float` | 최근 물가 상승률 (SMA) | `SensoryModule` (Gov) |
| `gdp_growth_rate` | `float` | 최근 GDP 성장률 (SMA) | `SensoryModule` (Gov) |
| `market_volatility` | `float` | 주식 시장 변동성 (VIX proxy) | `StockMarketTracker` (Optional) |
| `interest_rate_trend` | `float` | 금리 변화율 (Delta) | `Bank` |

### 2.2 Output: Dynamic Risk Modifier
기존 `risk_aversion`($\lambda$)에 곱해질 계수입니다.
- **Base State**: 1.0 (변화 없음)
- **Panic State**: > 1.0 (위험 회피 증가, 안전 자산 선호)

## 3. 알고리즘 및 로직 (Logic & Algorithms)

### 3.1 동적 위험 회피 계수 산출 (Dynamic Risk Aversion Calculation)

가계의 최종 위험 회피도 $\lambda_{effective}$는 다음과 같이 계산됩니다.

$$ \lambda_{effective} = \lambda_{base} \times (1.0 + \text{Stress}_{inflation} + \text{Stress}_{recession}) $$

#### 의사코드 (Pseudo-code)

```python
def calculate_effective_risk_aversion(base_lambda: float, context: MacroFinancialContext) -> float:
    # 1. 인플레이션 스트레스 (Target 2% 초과 시 공포 증가)
    CONST_INFLATION_TARGET = 0.02
    # 음수 인플레이션(디플레이션)은 현재 로직에서 공포 요인이 아니라고 가정 (혹은 별도 처리)
    inflation_excess = max(0.0, context.inflation_rate - CONST_INFLATION_TARGET)
    
    # Weight Tuning: 인플레이션 1% 초과 당 Lambda 10% 증가 (예시)
    # 10% Inflation -> 0.08 excess -> 0.8 stress -> Lambda 1.8x
    stress_inflation = inflation_excess * 10.0

    # 2. 경기 침체 스트레스 (역성장 시 공포 급증)
    stress_recession = 0.0
    if context.gdp_growth_rate < 0.0:
        # -5% Growth -> 0.05 abs -> 0.25 stress -> Lambda 1.25x
        stress_recession = abs(context.gdp_growth_rate) * 5.0

    # 3. 금리 변동성 (Optional)
    # 금리가 급격히 오르면 채권/주식 모두 악재 -> 현금 선호
    stress_rate = max(0.0, context.interest_rate_trend) * 2.0

    total_stress_multiplier = 1.0 + stress_inflation + stress_recession + stress_rate

    # 상한선(Cap) 적용 (너무 극단적인 회피 방지, 예: 최대 3배)
    # Lambda가 30.0을 넘어가면 투자가 사실상 0이 됨.
    CONST_MAX_MULTIPLIER = 3.0
    total_stress_multiplier = min(CONST_MAX_MULTIPLIER, total_stress_multiplier)

    return base_lambda * total_stress_multiplier
```

### 3.2 포트폴리오 최적화 파이프라인 수정 (Execution Pipeline)
`simulation/engine.py` 내 `run_tick` 루프에서 가계 의사결정 직전에 Context를 조립해야 합니다.

1.  **Context Assembly (Engine)**: `tracker.get_latest_indicators()` 및 `sensory_dto` 등을 활용하여 `MacroFinancialContext` 인스턴스 생성.
2.  **Injection (Household)**: `household.make_decision(...)` 호출 시 `macro_context`를 인자로 전달 (혹은 `market_data` 딕셔너리에 포함).
3.  **Calculation (PortfolioManager)**: `PortfolioManager.optimize_portfolio` 호출 전, `calculate_effective_risk_aversion`을 먼저 수행.
4.  **Optimization**: 보정된 $\lambda$를 사용하여 자산 배분 계산.

## 4. 예외 처리 (Exception Handling)
- **데이터 누락 (Early Ticks)**: 시뮬레이션 초기(Tick < 10)에는 SMA 데이터가 불충분하여 `0.0`으로 올 수 있음.
    - **Action**: 모든 Stress 요인이 0이 되므로 `Multiplier = 1.0` (정상 동작) 처리.
- **Extreme Value**: 인플레이션이 1000% 등 비정상 수치일 경우.
    - **Action**: `CONST_MAX_MULTIPLIER` (3.0)에 의해 상한선이 적용되므로 로직 붕괴 방지.

## 5. 검증 계획 (Verification Plan)
- **Test Case 1 (Normal)**: 인플레이션 2%, GDP 성장 3% → Multiplier 1.0 근사 확인.
- **Test Case 2 (Stagflation)**: 인플레이션 10%, GDP 성장 -2% → Multiplier 대폭 상승 확인 (> 1.5).
- **Simulation**: 'Chaos Injection' (Tick 200, 600) 발생 시 가계들의 주식 매도세(Safety Preference)가 관측되어야 함.

---

### [Mandatory Reporting]
**Jules Checkpoint**:
구현 중 발견되는 다음 항목을 `communications/insights/`에 반드시 보고하십시오:
1. **Flash Crash Risk**: 매크로 민감도(가중치) 설정이 너무 높아 작은 경제 변동에도 시장 붕괴를 유발하지 않는지?
2. **SoC Check**: `MacroFinancialContext` 데이터를 `Engine`에서 집계할 때, `TransactionProcessor`나 다른 모듈의 영역을 침범하지 않는지?
3. **Data Lag**: Sensory Module의 SMA(이동평균)가 너무 느려서 위기에 뒤늦게 반응하지 않는지?
```
