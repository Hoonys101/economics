# Phase 10 Specification: The Central Bank (Monetary Policy)

> **Goal**: Introduce a Central Bank agent that regulates the economy through interest rates, aimed at stabilizing inflation and unemployment (Dual Mandate).

---

## 1. System Architecture

### 1.1. The Central Bank Agent
- **Role**: `CentralBank` (Singleton Agent).
- **Responsibility**:
    1.  Monitor Macro-Economic Indicators (Inflation, GDP Gap, Unemployment).
    2.  Set the **Base Interest Rate** (`base_rate`) every tick (or period).
    3.  Act as "Lender of Last Resort" to Commercial Banks (Phase 11).

### 1.2. Transmission Mechanism (Dynamics)
The `base_rate` affects the economy through the `LoanMarket` and `Bank`:
- **Loan Rate**: `Bank` sets `loan_rate = base_rate + risk_premium + profit_margin`.
- **Deposit Rate**: `Bank` sets `deposit_rate = base_rate - spread`.
- **Behavioral Impact**:
    - **Households**:
        - High Rates -> Increase Savings (Delay Consumption), Reduce Borrowing.
        - Low Rates -> Increase Consumption, Increase Borrowing.
    - **Firms**:
        - High Rates -> Reduce Borrowing for Expansion/Payroll -> Lower Investment.
        - Low Rates -> Increase Borrowing -> Higher Investment.

---

## 2. Theoretical Model: The Taylor Rule

The Central Bank uses a modified **Taylor Rule** to decide the interest rate.

$$ i_t = \max(0, r^* + \pi_t + \alpha(\pi_t - \pi^*) + \beta(\log Y_t - \log Y^*)) $$

- $i_t$: Target Nominal Interest Rate.
- $r^*$: Neutral Real Interest Rate (Assumption: 2%).
- $\pi_t$: Current Inflation Rate (smoothed).
- $\pi^*$: Target Inflation Rate (Config: 2% or 0.02).
- $Y_t$: Current Real GDP.
- $Y^*$: Potential GDP (Estimated via EMA of past GDP).
- $\alpha$: Inflation Sensitivity (Config: 0.5).
- $\beta$: Output Gap Sensitivity (Config: 0.5).

---

## 3. Implementation Details

### 3.1. Config Constants (`config.py`)
```python
# Phase 10: Central Bank
CB_ENABLED = True
CB_UPDATE_INTERVAL = 10         # Ticks between rate updates (Policy Lag)
CB_INFLATION_TARGET = 0.02      # 2% Target
CB_NEUTRAL_RATE = 0.02          # 2% Real Neutral Rate
CB_TAYLOR_ALPHA = 1.5           # Aggressiveness vs Inflation
CB_TAYLOR_BETA = 0.5            # Aggressiveness vs Recession
```

### 3.2. Data Structures
- **`CentralBank` Class**: Inherits `BaseAgent` (or standalone).
    - `calculate_target_rate(inflation, gdp_growth)`
    - `publish_rate()` -> Updates `Simulation.base_rate`.

### 3.3. Integration Points
- **`Simulation`**: Holds `base_rate` state (accessible by all markets).
- **`Bank`**: Updates `loan_rate` and `deposit_rate` whenever `base_rate` changes.
- **`LoanMarket`**: Uses updated rates for new loan contracts.

---

## 4. Verification Plan

### 4.1. Scenario: Inflation Shock
- **Trigger**: Sudden supply shock (Production -50%) -> Price Spike.
- **Expected Reaction**:
    - Inflation $\uparrow$.
    - Central Bank raises `base_rate` $\uparrow$.
    - `Bank` raises `loan_rate` $\uparrow$.
    - Agents reduce borrowing/consumption.
    - Inflation cools down.

### 4.2. Scenario: Recession
- **Trigger**: Demand shock (Households assets wiped).
- **Expected Reaction**:
    - GDP $\downarrow$.
    - Central Bank cuts `base_rate` $\downarrow$ (Zero Lower Bound check).
    - Borrowing becomes cheaper -> Stimulus.
