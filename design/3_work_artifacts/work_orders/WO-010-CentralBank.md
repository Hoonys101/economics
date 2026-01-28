# Work Order: WO-010-CentralBank

**Target**: Jules (Implementation Agent)
**Phase**: 10 - Central Bank & Monetary Policy
**Status**: Ready for Development

---

## 1. Objective
Implement the `CentralBank` agent and the **Taylor Rule** logic to dynamically adjust interest rates based on inflation and GDP data. This connects the financial market (`Bank`) with the real economy through interest rate transmission.

## 2. Technical Requirements

### A. Configuration (`config.py`)
Add the following constants (referenced in Spec):
- `CB_UPDATE_INTERVAL`
- `CB_INFLATION_TARGET`
- `CB_TAYLOR_ALPHA`
- `CB_TAYLOR_BETA`

### B. Module: `simulation/agents/central_bank.py` (New)
Create `CentralBank` class:
- **Inputs**: `EconomicIndicatorTracker` (for Inflation, GDP).
- **Methods**:
    - `step(current_tick)`: Checks interval.
    - `calculate_rate()`: Implements Taylor Rule.
    - `get_base_rate()`: Returns current rate.

### C. Integration: `simulation/engine.py` & `bank.py`
1.  **Engine**: Initialize `CentralBank`. Call `central_bank.step()` in `run_tick`.
2.  **Bank**: Modify `Bank.update_rates()` to read `central_bank.get_base_rate()`.
    - `loan_rate = base_rate + spread`
    - `deposit_rate = base_rate - spread`

## 3. Safety Constraints
- **Zero Lower Bound (ZLB)**: Ensure `base_rate` never goes below 0.0 (unless we strictly want negative rates, but start with 0 floor).
- **Smoothing**: Don't jump rates wildy. Cap max change per update (e.g., +/- 0.25%).

## 4. Verification (`scripts/verify_monetary_policy.py`)
Create a test script that:
1.  Mocks `tracker` with high inflation data -> Asserts Rate Hike.
2.  Mocks `tracker` with recession data -> Asserts Rate Cut.
3.  Runs a small loop to see `Bank` rates update.

---
**Deliverable**: Push to branch `feature/phase10-central-bank`. Do NOT modify `main` directly.
