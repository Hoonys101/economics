modules/firm/api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Protocol, TypedDict

from modules.simulation.api import AgentID
from modules.system.api import MarketSnapshotDTO, GovernmentPolicyDTO

# ==============================================================================
# Firm State DTOs (Extended for Debt Awareness)
# ==============================================================================

@dataclass
class FirmFinancialHealthDTO:
    """
    Component DTO specifically for financial health metrics.
    Passed to AI Planner to evaluate solvency and borrowing capacity.
    """
    total_assets: int  # Pennies
    total_debt: int    # Pennies
    equity: int        # Pennies
    
    # Ratios
    debt_to_equity_ratio: float
    debt_to_asset_ratio: float
    current_ratio: float # Current Assets / Current Liabilities (Liquidity)
    
    # Service Burden
    interest_expense_last_tick: int # Pennies
    interest_coverage_ratio: float # EBIT / Interest Expense
    
    # Limits
    borrowing_capacity_remaining: int # Pennies
    credit_limit: int # Pennies
    is_solvent: bool
    
    # Strategic Flags
    is_in_debt_spiral: bool # Heuristic: Debt > Equity * 3 or similar
    can_afford_new_loan: bool

@dataclass
class FirmStateDTO:
    """
    Comprehensive snapshot of the Firm's state for the Decision Engine.
    Now includes explicit financial health data.
    """
    agent_id: AgentID
    tick: int
    sector: str
    
    # Financials
    cash: int # Pennies
    financial_health: FirmFinancialHealthDTO
    
    # Operations
    inventory_volume: float
    production_capacity: float
    employee_count: int
    wage_bill_per_tick: int
    
    # Market
    last_sales_volume: float
    market_share: float
    
    # Strategic
    current_goals: List[str] = field(default_factory=list)

# ==============================================================================
# AI Planner Interfaces
# ==============================================================================

@dataclass
class PlannerConfigDTO:
    """
    Configuration for the FirmSystem2Planner.
    """
    aggression_factor: float = 1.0
    risk_tolerance: float = 0.5
    
    # Debt Constraints
    max_safe_debt_to_equity: float = 2.0
    max_leverage_ratio: float = 0.8
    min_interest_coverage: float = 1.5
    
    # NPV Params
    hurdle_rate: float = 0.05

class IFirmPlanner(Protocol):
    """
    Interface for the AI Planning System.
    """
    def generate_intent(
        self, 
        state: FirmStateDTO, 
        market_snapshot: MarketSnapshotDTO,
        policy: GovernmentPolicyDTO
    ) -> Any: # Returns IntentDTO
        ...

```

design/3_work_artifacts/specs/wave6_ai_debt_aware_spec.md
```markdown
# Mission Spec: Wave 6 AI Debt Awareness (TD-AI-DEBT-AWARE)

## 1. Overview
This mission addresses the "Constraint Blindness" of the `FirmSystem2Planner`, where firms continue to propose aggressive expansion or R&D investments despite being in a debt spiral. This behavior causes "Intent Spamming" in logs (Finance Engine rejects orders) and leads to unrealistic bankruptcy cascades.

We will inject a `FirmFinancialHealthDTO` into the `FirmStateDTO`, populated by the Orchestrator (`Firm.py`), allowing the Planner (Stateless Engine) to perceive its debt burden and voluntarily switch to a "Deleverage" or "Survival" strategy.

## 2. Architecture & Design

### 2.1. Data Flow (SEO Pattern)
1.  **Orchestrator (`Firm.make_decision`)**:
    *   Accesses `FinancialComponent`.
    *   Calculates `total_debt`, `equity`, `debt_to_equity_ratio`.
    *   Constructs `FirmFinancialHealthDTO`.
    *   Embeds into `FirmStateDTO`.
2.  **Engine (`FirmSystem2Planner`)**:
    *   Receives `FirmStateDTO`.
    *   **Gatekeeper Logic**: Checks `financial_health.is_in_debt_spiral`.
    *   **Penalty Logic**: Adjusts NPV of investments based on `interest_coverage_ratio`.
3.  **Output**:
    *   If spiraling: Returns `HoldIntent` or `LiquidateAssetIntent` (Deleverage).
    *   If healthy: Returns `InvestmentIntent` (as before).

### 2.2. New DTO Structure
See `modules/firm/api.py` for full definition.
*   `FirmFinancialHealthDTO`: Encapsulates all debt metrics. This prevents polluting the main `FirmStateDTO` with raw accounting fields.

### 2.3. Logic Specification (Pseudo-code)

#### A. Orchestrator Logic (`modules/firm/agents/firm.py`)
```python
def _build_state_dto(self) -> FirmStateDTO:
    fin = self.financial_component
    debt = fin.get_total_liabilities()
    assets = fin.get_total_assets()
    equity = assets - debt
    
    # Handle ZeroDivisionError safely
    d_e_ratio = debt / equity if equity > 0 else 999.0
    
    health_dto = FirmFinancialHealthDTO(
        total_assets=assets,
        total_debt=debt,
        equity=equity,
        debt_to_equity_ratio=d_e_ratio,
        interest_expense_last_tick=fin.last_interest_payment,
        is_in_debt_spiral=(d_e_ratio > self.config.max_safe_debt_ratio),
        borrowing_capacity_remaining=fin.get_credit_limit() - debt,
        # ... populate other fields ...
    )
    
    return FirmStateDTO(..., financial_health=health_dto)
```

#### B. Planner Logic (`modules/firm/planning/firm_system2_planner.py`)
```python
def evaluate_strategy(self, state: FirmStateDTO, ...) -> Intent:
    # 1. Hard Constraint Check (Gatekeeper)
    if state.financial_health.is_in_debt_spiral:
        return self._plan_survival_strategy(state)

    # 2. Soft Constraint (NPV Adjustment)
    base_npv = self._calculate_base_npv(...)
    
    # Penalize risk if leverage is high
    risk_penalty = 0.0
    if state.financial_health.debt_to_equity_ratio > 1.0:
        risk_penalty = base_npv * 0.2
        
    final_score = base_npv - risk_penalty
    
    if final_score > 0:
        return InvestmentIntent(...)
    else:
        return HoldIntent(...)
```

## 3. Impact Analysis & Risks

### 3.1. Test Regressions (High Risk)
*   **Problem**: Adding `financial_health` to `FirmStateDTO` will break all existing tests that instantiate this DTO manually (e.g., `tests/modules/firm/test_planner.py`).
*   **Mitigation**: 
    1.  Update `tests/conftest.py` -> `firm_state_factory` to include a default `FirmFinancialHealthDTO`.
    2.  Use `factory` patterns in tests instead of raw constructor calls.

### 3.2. Config Dependency
*   **Problem**: Hardcoding "Safe Debt Ratio" is bad.
*   **Solution**: Add `max_safe_debt_to_equity` to `FirmConfigDTO` (loaded from `finance.yaml`).

### 3.3. SEO Violation Check
*   **Audit**: Does the Planner access `firm.financial_component`?
*   **Verdict**: No. All data is passed via `FirmFinancialHealthDTO`.

## 4. Verification Plan

### 4.1. Unit Tests (`tests/modules/firm/test_debt_awareness.py`)
*   **Test Case 1: Healthy Firm**: Input DTO with D/E = 0.5. Verify `InvestmentIntent` is possible.
*   **Test Case 2: Debt Spiral**: Input DTO with D/E = 5.0. Verify `InvestmentIntent` is BLOCKED, returns `Hold` or `Deleverage`.
*   **Test Case 3: NPV Penalty**: Compare NPV of identical projects for Low Debt vs High Debt firms. High Debt should have lower score.

### 4.2. Integration Verification
*   **Scenario**: Run `stress_scenario_100.py` (High Interest Rate).
*   **Success Criteria**:
    *   Firms stop expanding immediately when rates rise and debt service increases.
    *   Reduction in `FinanceEngine: Rejecting Order` logs.

## 5. Mandatory Reporting
*   **Action**: Create `communications/insights/wave6-ai-debt.md`.
*   **Content**: Document the new `FirmFinancialHealthDTO` structure, the configured debt thresholds, and the results of the regression tests.

```