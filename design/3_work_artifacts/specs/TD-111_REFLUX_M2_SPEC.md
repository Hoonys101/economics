# Spec: TD-111 - M2 Money Supply Calculation Remediation

## 1. Objective

This document provides the formal technical specification for remediating **TD-111**. The goal is to establish a correct and safe method for calculating the M2 money supply for economic reporting, without compromising the system's critical zero-sum asset integrity checks.

This specification documents the **existing, correct implementation** and serves as a strict guideline to prevent future architectural regressions.

## 2. 🚨 Architectural Mandate & Risk Analysis

The pre-flight audit has identified a critical architectural constraint that MUST be adhered to. Failure to do so will break asset leak detection and mask future bugs.

### 2.1. Critical Constraint: Separation of Concerns

There are two distinct functions for calculating money, each with a single, non-overlapping responsibility:

1.  **`WorldState.calculate_total_money()` -> For System Integrity ONLY.**
    -   **Purpose**: This function is the canonical zero-sum validator. It is designed to track every unit of currency in the simulation, including system-internal balances like `EconomicRefluxSystem` and `CentralBank`.
    -   **MANDATE**: **DO NOT MODIFY OR USE FOR ECONOMIC REPORTING.** Its output is intentionally different from M2 and is essential for detecting asset leaks. Using it for M2 reporting will produce incorrect economic data and create false-positive leak reports.

2.  **`EconomicIndicatorTracker.get_m2_money_supply()` -> For Economic Reporting ONLY.**
    -   **Purpose**: This function correctly calculates the M2 money supply as understood by economic agents (Households, Firms, etc.).
    -   **MANDATE**: This is the **sole method** to be used for any feature requiring M2 data, such as dashboards, reports, and economic analysis.

### 2.2. Identified Risks

-   **SRP Violation**: The previous misuse of `WorldState.calculate_total_money()` violated the Single Responsibility Principle, leading to TD-111. This spec enforces the separation.
-   **Circular Dependency**: A circular import risk exists between `WorldState` and `EconomicIndicatorTracker`. This is correctly mitigated using `if TYPE_CHECKING:` blocks, a pattern that must be maintained.

## 3. Implementation Details (As-Built)

This section documents the current, correct implementation as found in the codebase.

### 3.1. Correct M2 Calculation (`EconomicIndicatorTracker`)

The M2 money supply is calculated by summing the assets of all active economic agents. System-internal balances are explicitly excluded.

```python
# simulation/metrics/economic_tracker.py

def get_m2_money_supply(self, world_state: 'WorldState') -> float:
    """
    Calculates the M2 money supply for economic reporting.
    M2 = Household_Assets + Firm_Assets + Bank_Reserves + Government_Assets

    This calculation INTENTIONALLY EXCLUDES the EconomicRefluxSystem balance
    and the Central Bank's balance, as they represent money not yet realized
    by economic agents or are used for system-level integrity.
    """
    total = 0.0

    # 1. Households
    for h in world_state.households:
        if getattr(h, "is_active", True):
            total += h.assets

    # 2. Firms
    for f in world_state.firms:
        if getattr(f, "is_active", False):
            total += f.assets

    # 3. Bank Reserves
    if world_state.bank:
        total += world_state.bank.assets

    # 4. Government Assets
    if world_state.government:
        total += world_state.government.assets

    return total
```

### 3.2. Zero-Sum Integrity Check (`WorldState`)

The total system money includes all agent and system accounts to ensure no currency is created or destroyed unexpectedly.

```python
# simulation/world_state.py

def calculate_total_money(self) -> float:
    """
    Calculates the total money supply in the entire system for zero-sum validation.
    Money_Total = Agent_Assets + System_Account_Balances
    """
    total = 0.0
    # ... (sums assets from households, firms, bank, government) ...

    # 4. Reflux System Balance (Undistributed)
    if self.reflux_system:
        total += self.reflux_system.balance

    # ... (sums assets from central_bank) ...

    return total
```

## 4. API Specification

-   **Class**: `simulation.metrics.economic_tracker.EconomicIndicatorTracker`
-   **Method**: `get_m2_money_supply(self, world_state: 'WorldState') -> float`
    -   **Description**: Returns the M2 money supply for economic reporting.
    -   **Parameters**:
        -   `world_state` (`WorldState`): The current state of the simulation.
    -   **Returns**: (`float`) The calculated M2 money supply.

## 5. Verification & Consumer Update Plan

### 5.1. Verification Steps

To confirm the system is working as intended:

1.  Run a simulation for at least 10 ticks, or until `world_state.reflux_system.balance` is greater than 0.
2.  Pause the simulation and get access to the `world_state` and `tracker` instances.
3.  Execute the following calls:
    ```python
    ws_total = world_state.calculate_total_money()
    m2_total = tracker.get_m2_money_supply(world_state)
    reflux_balance = world_state.reflux_system.balance
    # May also need to account for central bank balance if it's non-zero
    cb_balance = world_state.central_bank.assets.get('cash', 0.0)
    ```
4.  Assert that the zero-sum total correctly accounts for the M2 supply plus the system balances:
    ```python
    # The zero-sum total MUST equal the M2 total plus all excluded system balances.
    assert abs(ws_total - (m2_total + reflux_balance + cb_balance)) < 1e-6
    ```

### 5.2. Consumer Update Checklist

All parts of the codebase that perform economic reporting must be audited and updated to use the correct method.

-   [ ] **`scripts/generate_phase1_report.py`**: Update any calls using `world_state.calculate_total_money` for reporting.
-   [ ] **`dashboard/app.py`**: Ensure all charts and metrics related to money supply use `tracker.get_m2_money_supply`.
-   [ ] **`analysis/` scripts**: Audit all scripts in this directory for misuse of the world state function.
-   [ ] **`tests/`**: Review all tests asserting money supply values. They must use the correct function and verification logic from section 5.1.
-   [ ] **`simulation/engine.py`**: Ensure the `money_supply` value passed to `tracker.track()` is the M2 value.

## 6. [Routine] Mandatory Reporting

-   Upon completion of the consumer update, document any new insights or discovered technical debt in `communications/insights/`.
-   Update the `design/TECH_DEBT_LEDGER.md` to change the status of **TD-111** to **`RESOLVED`**.
