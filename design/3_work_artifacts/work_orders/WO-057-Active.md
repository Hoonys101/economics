Here are the drafted artifacts for **The Great Redistribution**.

### 1. API Contract & DTOs
**File Path:** `modules/government/api.py`

```python
from typing import TypedDict, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

# ==============================================================================
# DTO Definitions
# ==============================================================================

@dataclass
class GovernmentStateDTO:
 """
 Sensory Module DTO.
 Transfers 10-tick SMA macro data to the Government Agent.
 """
 tick: int
 inflation_sma: float
 unemployment_sma: float
 gdp_growth_sma: float
 wage_sma: float
 approval_sma: float
 current_gdp: float

class DeficitStatusDTO(TypedDict):
 """
 Deficit Spending Status.
 """
 agent_id: int
 tick: int
 assets: float
 total_debt: float
 debt_to_gdp_ratio: float
 is_deficit_spending_active: bool
 deficit_limit_remaining: float

# ==============================================================================
# Interface Definitions
# ==============================================================================

class IGovernment(ABC):
 """
 Abstract Interface for Government Agent.
 """

 @abstractmethod
 def update_sensory_data(self, dto: GovernmentStateDTO) -> None:
 """
 Receives macro-economic data (sensory input) from the Engine.
 """
 ...

 @abstractmethod
 def provide_subsidy(self, target_agent: Any, amount: float, current_tick: int) -> float:
 """
 Provides subsidy to a target agent.

 [ Update]
 - If `DEFICIT_SPENDING_ENABLED` is True:
 - Allows `self.assets` to drop below zero up to `GDP * DEFICIT_LIMIT`.
 - Updates `self.total_debt`.
 - If False or Limit reached:
 - Returns 0.0 (Fiscal Cliff).
 """
 ...

 @abstractmethod
 def get_fiscal_status(self) -> DeficitStatusDTO:
 """
 Returns the current fiscal health and debt metrics.
 """
 ...

class ISmartLeviathanPolicy(ABC):
 """
 Interface for the AI Policy Actuator.
 """

 @abstractmethod
 def decide(self, government: Any, market_data: Dict[str, Any], current_tick: int) -> Dict[str, Any]:
 """
 Executes policy decisions.
 [ Update]
 - Must handle 'Emergency Mode' allowing budget multipliers up to 2.0.
 """
 ...
```

---

### 2. Implementation Specification
**File Path:** `design/specs/government_deficit_spec.md`

```markdown
# Spec: The Great Redistribution (Deficit Spending)

## 1. Overview
- **Goal**: Allow the Government to perform **Deficit Spending** (debt-financed stimulus) during economic downturns, breaking the rigid "Pay-as-you-go" constraint.
- **Scope**: `Government` agent logic, `SmartLeviathanPolicy` limits, and `config` parameters.
- **Constraint**: Debt must be capped at a percentage of GDP to prevent hyperinflation/infinite debt.

## 2. Configuration (`config.py`)

Add the following parameters to `Phase 7: Adaptive Fiscal Policy` section:

```python
# --- Deficit Spending ---
DEFICIT_SPENDING_ENABLED = True # Allow negative assets (Debt)
DEFICIT_SPENDING_LIMIT_RATIO = 0.30 # Max Debt = 30% of Nominal GDP
EMERGENCY_BUDGET_MULTIPLIER_CAP = 2.0 # Max multiplier during crisis (Bazooka)
NORMAL_BUDGET_MULTIPLIER_CAP = 1.0 # Normal max multiplier
```

## 3. Logic & Algorithms

### 3.1. Government Agent (`government.py`)

#### `provide_subsidy` (Revised)
The core change is in the funding check logic.

**Pseudo-code:**
```python
def provide_subsidy(self, target, amount, tick):
 # 1. Determine Effective Amount (Multiplier Logic - Existing)
 effective_amount = amount * (firm_multiplier if is_firm else welfare_multiplier)

 # 2. Check Deficit Capability
 is_deficit_enabled = config.DEFICIT_SPENDING_ENABLED
 current_gdp = self.sensory_data.current_gdp if self.sensory_data else 0.0
 debt_limit = current_gdp * config.DEFICIT_SPENDING_LIMIT_RATIO

 # 3. Calculate Projected State
 projected_assets = self.assets - effective_amount

 # 4. Validation
 if projected_assets < 0:
 if not is_deficit_enabled:
 return 0.0 # Rejection (Legacy Behavior)

 if abs(projected_assets) > debt_limit:
 log("FISCAL_CLIFF_REACHED", debt=abs(projected_assets), limit=debt_limit)
 return 0.0 # Rejection (Debt Ceiling)

 # 5. Execution
 self.assets -= effective_amount
 self.total_spent_subsidies += effective_amount
 self.total_money_issued += effective_amount
 self.expenditure_this_tick += effective_amount

 # 6. Update Debt State
 if self.assets < 0:
 self.total_debt = abs(self.assets)
 else:
 self.total_debt = 0.0

 return effective_amount
```

### 3.2. Smart Leviathan Policy (`smart_leviathan_policy.py`)

#### `decide` (Revised)
We need to relax the safety bounds when in "Emergency Mode".

**Pseudo-code:**
```python
def decide(self, government, market_data, tick):
 # ... (Existing Logic) ...

 # 4. The Safety Valve (Clipping & Bounds)

 # Detect Emergency (Simple Heuristic or via AI State)
 # For now, we use the `welfare_budget_multiplier` itself as a signal.
 # If AI requests huge expansion (e.g., > 1.5), and we are in deficit mode, allow it.

 max_budget_cap = config.NORMAL_BUDGET_MULTIPLIER_CAP

 # Emergency Condition: GDP Growth < -5% (Recession) OR Unemployment > 10%
 if government.sensory_data:
 if (government.sensory_data.gdp_growth_sma < -0.05) or \
 (government.sensory_data.unemployment_sma > 0.10):
 max_budget_cap = config.EMERGENCY_BUDGET_MULTIPLIER_CAP

 # Apply Limits
 budget_min = 0.1
 government.welfare_budget_multiplier = max(
 budget_min,
 min(max_budget_cap, government.welfare_budget_multiplier)
 )
 # Same for firm_subsidy_budget_multiplier
```

## 4. Verification Plan

### Test Case: `test_deficit_spending`
1. **Setup**: Initialize Government with `assets = 100`, `GDP = 1000`. Config `DEFICIT_LIMIT = 0.3` (Max Debt 300).
2. **Action 1 (Normal)**: Request Subsidy `50`.
 * Expect: `assets` = 50. Success.
3. **Action 2 (Into Debt)**: Request Subsidy `100`.
 * Expect: `assets` = -50. Success. `total_debt` = 50.
4. **Action 3 (Deep Debt)**: Request Subsidy `200`.
 * Expect: `assets` = -250. Success. `total_debt` = 250.
5. **Action 4 (Cliff)**: Request Subsidy `100`.
 * Projected `assets` = -350. (Limit is 300).
 * Expect: Return 0.0. `assets` remains -250.
6. **Verify**: Log contains "FISCAL_CLIFF_REACHED".

## 5. Mandatory Reporting (Routine)
- **Jules' Insight**: While implementing, if you find that `GDP` fluctuations cause sudden drops in the Debt Ceiling (forcing a pro-cyclical austerity), report this in `communications/insights/`. We might need a "Trailing Average GDP" for the limit calculation.
```
