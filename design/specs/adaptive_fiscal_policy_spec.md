# W-1. Spec: Phase 7 - Adaptive Fiscal Policy

## 1. Goal
정부가 **Output Gap**을 기반으로 재정정책을 자동 조정하는 **Counter-cyclical 자동 안정화 장치** 구현.

## 2. Implementation Details

### 2.1 New Config Parameters (`config.py`)
```python
# --- Phase 7: Adaptive Fiscal Policy ---
FISCAL_SENSITIVITY_ALPHA = 0.5          # Output gap → fiscal stance conversion
POTENTIAL_GDP_WINDOW = 50               # Ticks for moving average
TAX_RATE_MIN = 0.05
TAX_RATE_MAX = 0.30
TAX_RATE_BASE = 0.10                    # Neutral rate (boom/bust neutral)
DEBT_CEILING_RATIO = 1.0                # Max debt/GDP
FISCAL_STANCE_EXPANSION_THRESHOLD = 0.025   # +2.5% stance → expand
FISCAL_STANCE_CONTRACTION_THRESHOLD = -0.025 # -2.5% stance → contract
```

### 2.2 New Fields (`Government.__init__`)
```python
self.potential_gdp: float = 0.0
self.gdp_ema: float = 0.0                # Exponential Moving Average
self.fiscal_stance: float = 0.0
self.effective_tax_rate: float = getattr(config_module, "TAX_RATE_BASE", 0.1)
self.total_debt: float = 0.0            # Accumulated deficit
```

### 2.3 New Method: `adjust_fiscal_policy`
Location: `simulation/agents/government.py`

```python
def adjust_fiscal_policy(self, current_gdp: float) -> None:
    """Adjust fiscal policy based on Output Gap."""
    alpha = getattr(self.config_module, "FISCAL_SENSITIVITY_ALPHA", 0.5)
    window = getattr(self.config_module, "POTENTIAL_GDP_WINDOW", 50)
    
    # 1. Update Potential GDP (EMA)
    if self.potential_gdp == 0:
        self.potential_gdp = current_gdp
    else:
        ema_weight = 2 / (window + 1)
        self.potential_gdp = current_gdp * ema_weight + self.potential_gdp * (1 - ema_weight)
    
    # 2. Calculate Output Gap
    if self.potential_gdp > 0:
        output_gap = (current_gdp - self.potential_gdp) / self.potential_gdp
    else:
        output_gap = 0.0
    
    # 3. Set Fiscal Stance (Counter-cyclical: negative gap → positive stance)
    self.fiscal_stance = -alpha * output_gap
    
    # 4. Adjust Tax Rate
    base_rate = getattr(self.config_module, "TAX_RATE_BASE", 0.1)
    min_rate = getattr(self.config_module, "TAX_RATE_MIN", 0.05)
    max_rate = getattr(self.config_module, "TAX_RATE_MAX", 0.30)
    
    # Expansion stance → lower taxes; Contraction → higher taxes
    adjustment = self.fiscal_stance * 0.3  # 30% of stance affects rate
    self.effective_tax_rate = base_rate * (1 - adjustment)
    self.effective_tax_rate = max(min_rate, min(max_rate, self.effective_tax_rate))
```

### 2.4 Modify `calculate_income_tax`
Replace fixed `INCOME_TAX_RATE` with `self.effective_tax_rate`.

### 2.5 Dynamic `provide_subsidy` (Centralized Spending)
**All** spending (welfare, stimulus, infrastructure) must pass through this method to enforce the debt ceiling.

```python
def provide_subsidy(self, target_agent: Any, amount: float, current_tick: int):
    debt_ceiling = getattr(self.config_module, "DEBT_CEILING_RATIO", 1.0)
    current_debt_ratio = self.total_debt / max(self.potential_gdp, 1.0)
    
    # Check if we need to print money
    if self.assets < amount:
        # If debt ceiling reached, we CANNOT print more money
        if current_debt_ratio >= debt_ceiling:
            self.logger.warning(f"DEBT_CEILING_HIT | Ratio: {current_debt_ratio:.2f}. Blocking subsidy.")
            return 0.0
            
        # Deficit Spending (Money Printing)
        deficit = amount - self.assets
        self.assets += deficit
        self.total_debt += deficit
        self.logger.info(f"DEFICIT_SPENDING | Printed {deficit:.2f}. Total Debt: {self.total_debt:.2f}")

    # Final assets check (safety)
    actual_payment = min(amount, self.assets)
    if actual_payment <= 0: return 0.0
    
    self.assets -= actual_payment
    target_agent.assets += actual_payment
    # ... logging ...
    return actual_payment
```

### 2.6 Integration with Stimulus
`run_welfare_check` should call `provide_subsidy` without manually increasing `self.assets`.
The "GDP 5% drop" logic remains as a trigger, but its execution is now throttled by the **Debt Ceiling** within `provide_subsidy`.

## 3. Integration Points

| Method | Change |
|--------|--------|
| `run_welfare_check` | Call `adjust_fiscal_policy(current_gdp)` at start |
| `calculate_income_tax` | Use `self.effective_tax_rate` instead of config constant |
| `provide_subsidy` | Add debt ceiling check |

## 4. Verification Plan

### Unit Tests (`tests/test_fiscal_policy.py`)
1. `test_fiscal_expansion_on_recession`: GDP↓ → tax_rate↓
2. `test_fiscal_contraction_on_boom`: GDP↑ → tax_rate↑
3. `test_debt_ceiling_blocks_deficit`: debt/GDP > 1.0 → subsidy blocked
4. `test_potential_gdp_ema_update`: EMA converges correctly
