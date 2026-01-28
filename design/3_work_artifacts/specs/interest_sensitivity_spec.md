# W-1. Spec: Interest Sensitivity & Monetary Transmission

## 1. Goal
중앙은행의 금리 정책이 가계의 소비 및 저축 행동에 영향을 미치도록 **통화 정책 전파 경로(Monetary Transmission Mechanism)**를 `AIDrivenHouseholdDecisionEngine` 내에 구현합니다.

## 2. Core Logic: Dual Channel Transmission

금리(Nominal Rate)는 두 가지 경로를 통해 가계의 소비 성향(MPC)을 조절합니다.

### 2.1 Channel 1: Substitution Effect (Savings Incentive)
*   **Logic**: 실질 금리가 높을수록 미래 소비를 위해 현재 소비를 줄임.
*   **Target**: 주로 **자산가(Ant)** 성향이나 부채가 적은 계층.
*   **Formula**:
    $$r_{real} = i_{nominal} - \pi_{expected}$$
    $$Incentive = \max(0, (r_{real} - r_{neutral}) \times \beta_{sensitivity})$$
    *   $\beta_{sensitivity}$: Personality별 민감도 (Ant: 5.0, Grasshopper: 1.0)

### 2.2 Channel 2: Income Effect (Debt Burden)
*   **Logic**: 금리가 오르면 이자 비용이 증가하여 가처분 소득 감소 → 강제 소비 축소.
*   **Target**: **차입자(Grasshopper)** 성향이나 부채가 많은 계층.
*   **Formula**:
    $$DSR = \frac{\text{Daily Interest Burden}}{\text{Income Proxy (Assets, Wage)}}$$
    $$Penalty = \begin{cases} 0.1 & \text{if } DSR > 0.4 \\ 0.0 & \text{otherwise} \end{cases}$$

## 3. Implementation Details

### 3.1 `AIDrivenHouseholdDecisionEngine.make_decisions`

#### Step 1: Input Gathering
*   `nominal_rate`: `market_data['loan_market']['interest_rate']`
*   `expected_inflation`: `household.expected_inflation` (Phase 8)에서 평균값 산출.
*   `debt_data`: `market_data['debt_data'][household.id]` (Total Principal, Interest Burden)

#### Step 2: Calculate Modifiers

```python
# Pseudo-code Structure

# 1. Real Interest Rate
avg_expected_infl = sum(household.expected_inflation.values()) / len(...)
real_rate = nominal_rate - avg_expected_infl

# 2. Savings Incentive (Substitution Effect)
# Higher sensitivity for 'Ants' (Wealth Orientation)
sensitivity = 5.0 if household.value_orientation == "wealth_and_needs" else 1.0
savings_incentive = max(0.0, (real_rate - config.NEUTRAL_REAL_RATE) * sensitivity)

# 3. Debt Burden (Income Effect)
# Check DSR (Debt Service Ratio)
debt_burden = market_data['debt_data'].get(household.id, {}).get("daily_interest_burden", 0.0)
income_proxy = max(household.current_wage, household.assets * 0.01) # Wage or 1% of Assets
dsr = debt_burden / (income_proxy + 1e-9)

debt_penalty = 0.0
if dsr > config.DSR_CRITICAL_THRESHOLD: # e.g., 0.4
    debt_penalty = 0.2 # Reduce consumption aggressiveness significantly
```

#### Step 3: Apply to Action Vector
*   `consumption_aggressiveness`를 감소시킵니다.
    $$Agg_{final} = Agg_{raw} \times (1.0 - savings\_incentive - debt\_penalty)$$
*   **Subsistence Constraint**: 그러나 `survival_need`가 임계치(80+) 이상이면 감소시키지 않습니다 (굶어 죽을 순 없음).

## 4. Config Parameters
`config.py`에 다음 상수 추가 필요:

```python
NEUTRAL_REAL_RATE = 0.02 # 2%
DSR_CRITICAL_THRESHOLD = 0.4 # 40% of income used for interest
INTEREST_SENSITIVITY_ANT = 5.0
INTEREST_SENSITIVITY_GRASSHOPPER = 1.0
```

## 5. Verification Plan
1.  **Script**: `scripts/verify_monetary_transmission.py`
2.  **Test Case**:
    *   Set Inflation = 0.
    *   Force Central Bank Rate = 10% (High).
    *   Check if `Ant` households reduce consumption.
    *   Check if High-Debt `Grasshopper` households reduce consumption (due to DSR).
    *   Force Central Bank Rate = 0% (Low).
    *   Check if consumption recovers.
