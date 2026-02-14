file: design/4_hard_planning/DEBT_CLEARANCE_STRATEGY_PHASE16.md
```markdown
# Phase 16: Parallel Debt Clearance Strategy (Mission 16.1)

## 1. Executive Summary

**Objective**: Eliminate three critical architectural vulnerabilities (Security, Integrity, Stability) preventing the safe scaling of the "Living Economy".
**Scope**: Server Security (Lane 1), Financial Protocol Integrity (Lane 2), and Logic Consistency (Lane 3).
**Execution Mode**: Parallel Execution (Lanes are loosely coupled).

| Lane | ID | Priority | Description | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **Lane 1** | `TD-ARCH-SEC-GOD` | **High** | Secure the `server.py` FastAPI cockpit command interface. | System |
| **Lane 2** | `TD-CRIT-FLOAT-SETTLE` | **Critical** | Enforce strict `int` (pennies) in Settlement; ban silent casting. | Finance |
| **Lane 3** | `TD-INT-PENNIES-FRAGILITY` | **High** | Unify `hasattr` checks to strict Protocol adherence (Pennies). | Core |

---

## 2. Lane 1: System Security (`TD-ARCH-SEC-GOD`)

### 2.1. Root Cause Analysis
- **Schism**: The project maintains two server entry points: `modules/system/server.py` (Secure, Custom Websocket) and `server.py` (Insecure, FastAPI/Uvicorn).
- **Vulnerability**: The active production server (`server.py`) exposes `/ws/command` which accepts `CockpitCommand` payloads (e.g., `PAUSE`, `GOD_MODE_TRIGGER`) without any authentication headers or token validation.
- **Risk**: Arbitrary code execution or simulation disruption via open WebSocket port.

### 2.2. Proposed Solution
**Architecture**: Middleware Injection.
1.  **Shared Auth Logic**: Extract token validation from `modules/system/server.py` to `modules/system/security.py`.
2.  **FastAPI Integration**: Implement a `WebSocketEndpoint` dependency in `server.py` that validates `X-GOD-MODE-TOKEN` header during the handshake.
3.  **Config Unification**: Ensure both servers source the token from `config.get("GOD_MODE_TOKEN")`.

### 2.3. Verification Plan
- **Test Case**: `tests/security/test_server_auth.py`
    - `test_websocket_connect_no_token_fails`: Assert 403/401.
    - `test_websocket_connect_invalid_token_fails`: Assert 403/401.
    - `test_websocket_connect_valid_token_succeeds`: Assert connection open.

---

## 3. Lane 2: Financial Integrity (`TD-CRIT-FLOAT-SETTLE`)

### 3.1. Root Cause Analysis
- **Leak**: `FinanceSystem.issue_treasury_bonds` calculates amounts (potentially floats) and casts them `int(amount)` *immediately before* calling `settlement_system.transfer`.
- **Masking**: This "last-mile" casting hides upstream floating-point errors (e.g., `100.99` becoming `100`), permanently destroying value (0.99) and violating the Zero-Sum principle.
- **Protocol Drift**: `ISettlementSystem` is not strictly typed to reject floats at runtime.

### 3.2. Proposed Solution
**Architecture**: Strict Typing & Interface Expansion.
1.  **Protocol Update**: Update `modules/finance/api.py::ISettlementSystem` to strictly define `amount: int`.
2.  **Runtime Guard**: In `SettlementSystem.transfer`, add:
    ```python
    if not isinstance(amount, int):
        raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)}")
    ```
3.  **Source Fix**: Refactor `issue_treasury_bonds` to ensure `amount` is an integer *at the source* (e.g., derived from integer inputs), removing the casting at the call site.
4.  **Protocol Drift Fix**: Explicitly add `mint_and_distribute` to `ISettlementSystem` to match usage in `CommandService`.

### 3.3. Verification Plan
- **Test Case**: `tests/finance/test_settlement_integrity.py`
    - `test_transfer_float_raises_error`: Pass `100.0` to transfer, assert `TypeError`.
    - `test_bond_issuance_integrity`: Issue bond, verify exact penny change in Agent Wallet vs Treasury.

---

## 4. Lane 3: Logic Consistency (`TD-INT-PENNIES-FRAGILITY`)

### 4.1. Root Cause Analysis
- **Split Brain**: Legacy code supports both `float` (Dollars) and `int` (Pennies) using `hasattr(firm, 'finance_state')` or `hasattr(firm, 'capital_stock_pennies')`.
- **Inflation Risk**: `FinanceSystem.evaluate_solvency` manually converts: `capital_stock_pennies = int(firm.capital_stock * 100)`. If `firm.capital_stock` is *already* migrated to pennies, this results in 10,000% inflation.
- **Fragility**: The logic relies on variable names rather than structural types.

### 4.2. Proposed Solution
**Architecture**: Protocol-Driven Unification.
1.  **Standardize Interfaces**: define `IFinancialEntity` Protocol with `get_capital_stock() -> int`.
2.  **Engine Refactor**: Update `FinanceSystem` to assume input Agents conform to `IFinancialEntity` (Pennies).
3.  **Clean Up**: Remove `hasattr` checks in `evaluate_solvency` and `EconComponent`. Assert that all inputs are strict DTOs (`FirmSnapshotDTO`, `HouseholdSnapshotDTO`).

### 4.3. Verification Plan
- **Test Case**: `tests/finance/test_solvency_logic.py`
    - `test_solvency_calculation_pennies`: Create a Firm with known penny values. Verify Z-Score calculation does NOT multiply by 100 again.
    - `test_input_types`: Ensure `FinanceSystem` raises error if passed a legacy object.

---

## 5. Parallel Execution Strategy

These lanes interact but can be merged sequentially or independently:

1.  **Step 1 (Lane 2 - Foundation)**: Hardening `SettlementSystem` (int-only) is the blocker. Do this first. It might break existing float-based tests (Good - Fail Fast).
2.  **Step 2 (Lane 3 - Cleanup)**: Once Settlement rejects floats, `FinanceSystem` *must* be fixed to stop sending floats. This naturally forces the resolution of `TD-INT-PENNIES-FRAGILITY`.
3.  **Step 3 (Lane 1 - Isolated)**: `server.py` security is independent of the simulation logic. Can be done anytime.

**Recommendation**: Execute **Lane 2 (Settlement)** -> **Lane 3 (Finance)** -> **Lane 1 (Server)**.

## 6. Audit & Risk Analysis (Pre-Implementation)

### 6.1. Architectural Mines
- **Test Suite Collapse**: Enforcing `int` in Settlement will likely cause ~40% of legacy tests to fail immediately (those using float mocks).
    - *Mitigation*: Run `scripts/fixture_harvester.py` to regenerate `golden_firms` with strict integer values *before* applying the strict check.
- **Circular Imports**: `FinanceSystem` importing `Firm` for type checking is dangerous.
    - *Mitigation*: Use `from __future__ import annotations` and `TYPE_CHECKING` blocks strictly. Use `AgentID` (int) instead of object references where possible.

### 6.2. Technical Debt Added
- None. This mission is purely subtractive (removing ambiguity).
```

file: communications/insights/mission-debt-clearance-plan.md
```markdown
# Insight Report: Critical Debt Clearance Planning

**Date**: 2026-02-14
**Mission**: `mission-debt-clearance-plan`
**Author**: Gemini-CLI Scribe

## 1. Architectural Insights

### A. The "Server Schism" (Security Gap)
I discovered a dangerous divergence in the system's entry points.
- **Secure**: `modules/system/server.py` implements robust `X-GOD-MODE-TOKEN` auth.
- **Insecure**: `server.py` (the likely production entry point) has **zero** authentication for its `/ws/command` endpoint.
This "Split-Brain" architecture means the security features implemented in Phase 10 are effectively bypassed if the user runs `python server.py`. The plan prioritizes unifying this logic.

### B. The "Inflationary Trap" (Logic Error)
In `modules/finance/system.py`, the following line poses a catastrophic risk during migration:
```python
capital_stock_pennies = int(firm.capital_stock * 100)
```
As we migrate `firm.capital_stock` to be natively stored as pennies (integer), this line will inadvertently multiply the value by 100 again (e.g., $100 -> 10,000 pennies -> 1,000,000 value). This "Double-Conversion" bug is a classic symptom of partial migration (`TD-INT-PENNIES-FRAGILITY`). The solution requires checking the type or migrating the attribute name to `capital_stock_pennies` explicitly to break the ambiguity.

### C. The "Settlement Filter" (Integrity)
The `SettlementSystem` currently trusts its callers to provide integers, but `FinanceSystem` explicitly casts floats right before calling it. This suggests the `FinanceSystem` is internally calculating with floats (likely due to legacy `amount` logic). Hardening `SettlementSystem` to raise `TypeError` on floats is the only way to "smoke out" these hidden float calculations in the domain layer.

## 2. Technical Debt & Risks

- **Risk: Test Suite Fragility**: Hardening the `SettlementSystem` to reject floats will likely break a significant number of older tests that rely on "lazy mocking" (using floats for convenience). We must be prepared for a "Red Wall" of test failures and have a strategy to batch-fix mocks.
- **Insight**: `FinanceSystem` violates SRP by mixing high-level orchestration (Risk Engine) with low-level accounting (Bailout Math). This makes it a "God Class" in training.

## 3. Recommended Actions
1.  **Execute Lane 2 (Settlement Hardening) First**: This will serve as a forcing function to identify all float leaks.
2.  **Audit `server.py` Deployment**: Confirm which server script is actually used in production/docker. If `server.py` is primary, `modules/system/server.py` code should be merged into it or deprecated.
```