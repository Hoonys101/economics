# Insight Report: Monetary Leak Fixes

## 1. Phenomenon
The simulation exhibited a systemic monetary leak where the total money supply (M2) was slowly drifting downwards over long durations, interspersed with occasional sharp drops. This was identified in `REPORT_MONEY_LEAK_AUDIT.md`.

## 2. Cause
Two distinct causes were identified:
1.  **Inheritance Rounding Error**: `DemographicManager.handle_inheritance` used floating-point arithmetic to calculate inheritance shares. The logic `floor(share * 100) / 100` resulted in truncation. While a remainder mechanism existed, it was susceptible to floating-point drift (`net_estate - distributed`), causing small fractional amounts (cents) to vanish during distribution.
2.  **Non-Atomic Transfers**: `SettlementSystem.transfer` lacked atomicity. It performed `debit_agent.withdraw()` followed by `credit_agent.deposit()`. If the deposit operation failed (e.g., due to an exception in the receiver's logic), the withdrawal was not reversed, causing the funds to be destroyed.

## 3. Solution
### 3.1. Integer-Based Inheritance Distribution
The `handle_inheritance` method in `simulation/systems/demographic_manager.py` was refactored to use integer arithmetic (cents) for all calculations.
-   Converted `net_estate` to `cents` (int).
-   Calculated `share_cents` using integer division `//`.
-   Calculated `remainder_cents` using modulo `%`.
-   Distributed `share_cents` to all heirs, and added `remainder_cents` to the last heir.
-   Converted back to float only for the final `transfer` call.
-   This guarantees `Sum(distributed_amounts) == net_estate` exactly.

### 3.2. Atomic Rollback in Settlement
The `transfer` method in `simulation/systems/settlement_system.py` was refactored to implement a rollback mechanism.
-   Separated `withdraw` and `deposit` into distinct `try...except` blocks.
-   If `deposit` fails, a `SETTLEMENT_ROLLBACK` event is triggered.
-   The system attempts to `deposit` the withdrawn amount back to the `debit_agent`.
-   If the rollback fails (catastrophic), a `SETTLEMENT_FATAL` log is recorded.

## 4. Verification
-   **Reproduction Script**: A script `verify_fix.py` was created to simulate the failure modes. It confirmed that:
    -   Inheritance distribution is now exact (Sum of heirs' assets = Parent's assets).
    -   Failed transfers result in a successful rollback (Sender's assets are restored).
-   **Unit Tests**: Added a new test case `test_transfer_rollback` to `tests/unit/systems/test_settlement_system.py`, which passes.

## 5. Technical Debt & Lessons Learned
-   **Test Rot**: `tests/unit/systems/test_inheritance_manager.py` fails because it tests a mocked `SettlementSystem` interaction that `InheritanceManager` (Phase 22) does not perform. `InheritanceManager` seems to generate `Transaction` objects instead of calling `transfer`. This indicates a divergence between the test, the legacy manager, and the active `DemographicManager` logic.
-   **Defensive Coding**: Financial systems must always assume operations can fail. Atomic transactions (or at least compensatable ones like rollbacks) are mandatory for money conservation.
-   **Floating Point**: Avoid floating-point arithmetic for financial distribution logic. Always use integers (lowest denomination) for allocation algorithms.
