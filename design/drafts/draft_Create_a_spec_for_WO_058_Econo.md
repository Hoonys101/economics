Here is the drafted specification and API contract for **WO-058 Economic CPR**.
I have designed this as a standalone module `modules/cpr` that acts as a sub-system of the Government/Central Bank, strictly adhering to the SoC principle.

### 1. File: `design/specs/economic_cpr_spec.md`

```markdown
# WO-058: Economic CPR (Emergency Stabilization Protocol)

## 1. Overview
The **Economic CPR (Cardiopulmonary Resuscitation)** system is an automated failsafe mechanism designed to detect "Systemic Cardiac Arrest" (zero trade volume, deflationary spirals, or mass liquidity crises) and inject emergency liquidity to restart the economic circulation.

## 2. Problem Statement
- **Velocity Trap**: In extreme scenarios, money velocity approaches zero. Households hoard cash due to fear, and firms stop production due to lack of sales.
- **Deadlock**: The economy freezes; agents have needs but no liquidity to transact.
- **Manual Intervention Required**: Currently, these states require a simulation restart.

## 3. Objectives
1.  **Automated Detection**: Monitor `EconomicIndicatorData` for vital signs (Velocity, Trade Volume, Unemployment).
2.  **Surgical Injection**: Provide liquidity **only** to viable agents (e.g., "Too Big To Fail" firms or Starving Households) rather than blind inflation.
3.  **Refractory Period**: Prevent hyperinflation loops by enforcing a cooldown period after intervention.

## 4. Data Structures & Interface (Contract)

### 4.1. Input: `EconomicVitalSigns` (DTO)
- Derived from `EconomicIndicatorData` (dtos.py).
- **Critical Metrics**:
    - `trade_volume_sma`: 10-tick Simple Moving Average of trade volume.
    - `bankruptcy_rate_velocity`: Rate of change in bankruptcy.
    - `deflation_index`: Persistence of price drops.

### 4.2. Output: `CPRInterventionPlan` (DTO)
- **Target**: List of Agent IDs (Households/Firms).
- **Amount**: Cash to inject per agent.
- **Reason**: String (Log purpose).
- **Method**: Enum (`HELICOPTER_DROP`, `BAILOUT`, `GOVT_PURCHASE`).

## 5. Logic & Algorithms (Pseudo-code)

### 5.1. Detection Logic (The Monitor)
```python
CONST_TRADE_VOLUME_THRESHOLD = 5.0  # Minimal functional economy
CONST_BANKRUPTCY_PANIC_THRESHOLD = 0.20 (20%)

def check_vital_signs(vitals: EconomicVitalSigns) -> CPRTriggerLevel:
    if vitals.trade_volume_sma < CONST_TRADE_VOLUME_THRESHOLD:
        return CRITICAL (Cardiac Arrest)
    
    if vitals.unemployment_rate > 0.50 and vitals.gdp_growth < -0.10:
        return SEVERE (Shock)

    return NORMAL
```

### 5.2. Intervention Logic (The Defibrillator)
```python
def execute_cpr(trigger_level: CPRTriggerLevel, agents: AgentRepository):
    if in_cooldown_period():
        return

    plan = CPRInterventionPlan()

    if trigger_level == CRITICAL:
        # Strategy A: Demand-Side Shock (Helicopter Money)
        # Target: Bottom 50% of households by assets
        targets = select_poorest_households(agents, percentile=50)
        amount = calculate_survival_cost(30_ticks)
        plan.add(targets, amount, HELICOPTER_DROP)

    elif trigger_level == SEVERE:
        # Strategy B: Supply-Side Life Support (Bailout)
        # Target: Insolvency but High Productivity (Viable Firms)
        targets = select_viable_bankrupt_firms(agents)
        amount = calculate_debt_relief(targets)
        plan.add(targets, amount, BAILOUT)

    apply_injection(plan)
    activate_cooldown(ticks=100)
```

## 6. Exception Handling
- **Hyperinflation Risk**: If `CPI` growth > 10% per tick, **DISABLE** CPR regardless of other signals.
- **Zero Agents**: If no agents exist, log error and do nothing.

## 7. Verification Plan
- **Test Case 1 (Freeze)**: Artificially set all agent assets to 0. Verify CPR triggers and injects cash.
- **Test Case 2 (Golden Sample)**: Verify `EconomicIndicatorData` shows a "V-shaped" recovery in Trade Volume post-injection.

## 8. Insights & Tech Debt Reporting (Mandatory)
- **Insight**: Currently, bailouts are free money. Future versions should treat them as "Loans" that the government recalls later (Fiscal Policy).
- **Debt**: The `select_viable_bankrupt_firms` logic relies on `firm.valuation` which is primitive. Needs a better solvency metric.
```

---

### 2. File: `modules/cpr/api.py`

```python
"""
WO-058: Economic CPR Module Interface.
Defines the contract for Emergency Economic Stabilization.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Protocol
from enum import Enum

# Import Common DTOs
# In a real scenario, we might import from core.dtos or simulation.dtos
# For this file generation, we define necessary structures here or assume imports.
from simulation.dtos import EconomicIndicatorData

class CPRTriggerLevel(Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    SEVERE = "SEVERE"     # Liquidity Crisis
    CRITICAL = "CRITICAL" # Economic Cardiac Arrest (Zero Velocity)

class InterventionType(Enum):
    HELICOPTER_DROP = "HELICOPTER_DROP" # Cash to Households
    BAILOUT = "BAILOUT"                 # Cash to Firms
    ASSET_PURCHASE = "ASSET_PURCHASE"   # Govt buys Inventory

@dataclass
class CPRConfiguration:
    """Thresholds for triggering CPR."""
    min_trade_volume_sma: float = 10.0
    max_unemployment_panic: float = 0.40
    min_liquidity_ratio: float = 0.05
    cooldown_ticks: int = 100
    inflation_lockout_threshold: float = 0.15 # Disable if inflation > 15%

@dataclass
class EconomicVitalSigns:
    """Normalized input data for the CPR Monitor."""
    tick: int
    trade_volume_sma_10: float
    unemployment_rate: float
    avg_household_liquidity: float
    bankruptcy_rate_velocity: float
    cpi_growth_rate: float

@dataclass
class InterventionAction:
    """A specific injection command."""
    target_agent_id: int
    agent_type: str # "FIRM" or "HOUSEHOLD"
    amount: float
    intervention_type: InterventionType
    reason: str

@dataclass
class CPRResultDTO:
    """Result of a CPR cycle."""
    tick: int
    trigger_level: CPRTriggerLevel
    actions_taken: List[InterventionAction]
    total_injected_liquidity: float
    is_locked_out: bool = False # Due to inflation or cooldown

class ICPRMonitor(Protocol):
    """Interface for detecting economic health."""
    
    def analyze_vitals(self, indicators: EconomicIndicatorData, history: List[EconomicIndicatorData]) -> CPRTriggerLevel:
        """
        Analyzes economic indicators to determine the emergency level.
        """
        ...

class ICPRDefibrillator(Protocol):
    """Interface for executing the intervention."""
    
    def calculate_intervention(self, level: CPRTriggerLevel, agents: Dict[int, Any]) -> List[InterventionAction]:
        """
        Calculates who gets what based on the trigger level.
        """
        ...
        
    def apply_intervention(self, actions: List[InterventionAction], government_agent: Any) -> float:
        """
        Executes the money transfer from Government to Agents.
        Returns total amount injected.
        """
        ...

# --- Stub for Implementation Reference ---
# These functions should be implemented in modules/cpr/service.py
#
# def create_cpr_engine(config: CPRConfiguration) -> ICPRDefibrillator:
#     ...
```

I have created the `spec.md` and `api.py` specifically for the **Economic CPR** system.
- **DTO Compliance**: Defined `EconomicVitalSigns` and `InterventionAction` to ensure strict typing.
- **SoC**: Separated the *Diagnosis* (`ICPRMonitor`) from the *Treatment* (`ICPRDefibrillator`).
- **Safe-guards**: Included `inflation_lockout_threshold` in the configuration to prevent the CPR from worsening hyperinflation.

Please confirm if you wish to proceed with the implementation (Phase W-2) based on these contracts.
