modules/governance/judicial/api.py
```python
from typing import TypedDict, List, Optional, Protocol, Dict
from dataclasses import dataclass

# Common/System Imports (Assumed available based on context)
from modules.system.api import AgentID
from modules.finance.api import Currency, AssetID

# DTOs
@dataclass
class JudicialConfigDTO:
    """Configuration for the Judicial System."""
    seizure_threshold: int = 0
    legal_fee_percent: float = 0.0
    bankruptcy_threshold: int = -1000  # Debt level triggering bankruptcy

@dataclass
class SeizureRequestDTO:
    """DTO for requesting asset seizure."""
    debtor_id: AgentID
    creditor_id: AgentID
    target_amount: int
    currency: Currency
    loan_id: str

@dataclass
class SeizureResultDTO:
    """Result of a seizure operation."""
    seized_cash: int
    seized_stocks_value: int
    seized_inventory_value: int
    remaining_debt: int
    is_fully_recovered: bool
    liquidated_assets: Dict[str, int]  # Details of what was sold

class IJudicialSystem(Protocol):
    """
    Interface for the Judicial System.
    Orchestrates debt recovery and bankruptcy proceedings.
    """

    def handle_default(self, event: 'LoanDefaultedEvent') -> SeizureResultDTO:
        """
        Process a loan default event using the Waterfall Recovery Logic.
        1. Cash Seizure
        2. Stock Seizure (Liquidation/Transfer)
        3. Inventory Seizure (Liquidation)
        """
        ...

    def assess_solvency(self, agent_id: AgentID) -> bool:
        """
        Check if an agent is solvent based on SSoT balances and assets.
        """
        ...

# Events (Re-defining for API completeness, though likely in events module)
class LoanDefaultedEvent(TypedDict):
    event_type: str  # "LOAN_DEFAULTED"
    tick: int
    agent_id: AgentID
    loan_id: str
    defaulted_amount: int  # Pennies
    creditor_id: AgentID

class DebtRestructuringRequiredEvent(TypedDict):
    event_type: str # "DEBT_RESTRUCTURING_REQUIRED"
    tick: int
    debtor_id: AgentID
    creditor_id: AgentID
    remaining_debt: int
    loan_id: str

```

design/3_work_artifacts/specs/modernize_regression_tests_spec.md
```markdown
# Spec: Modernize General Behavioral Regressions

## 1. Overview
This specification addresses critical regressions in the `JudicialSystem` and `ProductionEngine`. The primary goal is to enforce the **Single Source of Truth (SSoT)** pattern for all financial assertions and ensure deterministic manufacturing ratios in production logic.

### 1.1 Goals
- **Judicial System**: Refactor `handle_default` to query `SettlementSystem` directly for balances, removing reliance on stale `Agent` state.
- **Production Engine**: Standardize capital depreciation and input/output calculations to use strict integer arithmetic (pennies).
- **Testing**: Update regression tests to assert against the SSoT (`SettlementSystem`) and eliminate `Agent.assets` side-effect mocks.

## 2. Debt Review (Mandatory)
- **Status**: **RESOLVE**. This spec directly addresses "TD-045: Mock Object Drift in Judicial Tests" and "TD-092: Non-deterministic Float Math in Production".
- **Risk**: Low. This is a refactoring of internal logic and tests.
- **Ledger Action**: Upon completion, close TD-045 and TD-092 in `TECH_DEBT_LEDGER.md`.

## 3. Detailed Design

### 3.1 Judicial System: Waterfall Recovery Logic
The `JudicialSystem` acts as an Orchestrator. It must not rely on `agent.get_balance()`.

**Logic Flow (Pseudo-code):**
```python
def handle_default(self, event: LoanDefaultedEvent) -> SeizureResultDTO:
    remaining_debt = event['defaulted_amount']
    seized_total = 0
    
    # Step 1: Cash Seizure (Direct from SSoT)
    # Query SettlementSystem directly
    debtor_balance = self.settlement_system.get_balance(event['agent_id'], DEFAULT_CURRENCY)
    cash_seize_amount = min(debtor_balance, remaining_debt)
    
    if cash_seize_amount > 0:
        self.settlement_system.transfer(
            source=event['agent_id'],
            dest=event['creditor_id'],
            amount=cash_seize_amount,
            memo=f"Seizure for Loan {event['loan_id']}"
        )
        remaining_debt -= cash_seize_amount
        seized_total += cash_seize_amount

    # Step 2: Stock Seizure (If debt remains)
    if remaining_debt > 0:
        # Fetch portfolio via ShareholderRegistry (SSoT for stocks)
        stocks = self.shareholder_registry.get_portfolio(event['agent_id'])
        # Logic to transfer stocks at current market valuation
        # ...

    # Step 3: Inventory Seizure (If debt remains)
    if remaining_debt > 0:
        # Logic to liquidate inventory
        # ...

    # Emit Restructuring Event if debt still remains
    if remaining_debt > 0:
        self.event_bus.publish(DebtRestructuringRequiredEvent(...))

    return SeizureResultDTO(...)
```

### 3.2 Production Engine: Manufacturing Ratios
Ensure depreciation and productivity uses integer math.

**Logic Updates:**
- **Capital Depreciation**: `floor(capital_stock * depreciation_rate_basis_points / 10000)`
- **Productivity**: Ensure `labor_skill` and `technology_factor` result in a deterministic integer output quantity when applied to inputs.

## 4. Verification Plan

### 4.1 New Test Cases
Create `tests/unit/governance/test_judicial_ssot.py`:
- **test_waterfall_cash_only_ssot**: Setup `SettlementSystem` with 5000 pennies. Default 1000. Assert `SettlementSystem` balance becomes 4000. DO NOT check `Agent.assets`.
- **test_production_integer_depreciation**: Input capital 100,000. Rate 0.015 (1.5%). Assert depreciation is exactly 1,500.

### 4.2 Existing Test Impact
- **Refactor `tests/unit/governance/test_judicial_system.py`**:
    - Remove `MockAgent._assets`.
    - Replace `agent.assets` assertions with `settlement_system.get_balance.assert_called_with(...)` or state verification.
    - **CRITICAL**: Ensure `SettlementSystem` mock in `conftest.py` simulates balance updates if using `MagicMock`, or use a verified fake.

### 4.3 Integration Check
- Run `tests/integration/test_bankruptcy_flow.py` (if exists) or create a script to verify a firm going bankrupt correctly transfers assets to creditors without "creating" money (Zero-Sum check).

## 5. Mocking Guide
- **Use `tests/conftest.py` fixtures**: `mock_settlement_system` should be strict.
- **Forbidden**: `agent.assets = 500`.
- **Required**: `settlement_system.get_balance.return_value = 500`.

## 6. Pre-Implementation Risk Analysis
- **Circular Dependency**: `JudicialSystem` needs `SettlementSystem`. Ensure `SettlementSystem` does not import `JudicialSystem`.
- **Breaking Changes**: Changing `ProductionEngine` math might alter simulation trajectory slightly (Butterfly Effect). Acceptable for "Modernization" but requires explicit mention in CHANGELOG.

## 7. Mandatory Reporting Instruction
**IMMEDIATELY** create the file `communications/insights/modernize-regression-tests.md` with the following content structure:

```markdown
# Insight Report: Modernize Regression Tests

## Architectural Insights
- Identified dependence on `MockAgent` state in Judicial tests as a violation of SSoT.
- Production Engine float math is a source of non-determinism.

## Technical Debt
- [Resolving] TD-045: Mock Object Drift.
- [Resolving] TD-092: Non-deterministic Float Math.

## Test Evidence
(Paste pytest output here after implementation)
```
```