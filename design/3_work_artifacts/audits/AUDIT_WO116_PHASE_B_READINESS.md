# Report: WO-116 Phase B Readiness Analysis

## Executive Summary

The codebase is partially prepared for the Tick Sequence Normalization outlined in WO-116 Phase B. While Phase A introduced critical abstractions like the `SettlementSystem` and centralized some financial logic in `FinanceDepartment`, numerous asset transfers (taxes, welfare, interest, dividends) still occur directly within the main tick loop, outside the designated `_phase_transactions`. Moving most of these is feasible, but a critical dependency exists: Corporate Tax is calculated and paid *after* the transaction phase, making its direct inclusion impossible without re-sequencing core simulation logic like firm production.

## Detailed Analysis

The following asset transfers have been identified outside the `_phase_transactions` block in `simulation/tick_scheduler.py`.

| # | Transfer Type | Location (Function) | Method | File & Line | Status |
|---|---|---|---|---|---|
| 1 | Bank Interest & Profit | `bank.run_tick` | `settlement_system.transfer` | `bank.py:L316` | ⚠️ **Movable** |
| 2 | Private Firm Profit | `firm.distribute_profit` | `settlement_system.transfer` | `components/finance_department.py:L268`| ⚠️ **Movable** |
| 3 | Inheritance/Liquidation | `lifecycle_manager.execute` -> `process_death` | `settlement_system.transfer` | `systems/inheritance_manager.py:L218` | ⚠️ **Movable** |
| 4 | M&A Payments | `ma_manager.process...` -> `_execute_merger`| `settlement_system.transfer` | `systems/ma_manager.py:L207` | ⚠️ **Movable** |
| 5 | Sovereign Debt Service | `finance_system.service_debt` | `_transfer` (via SettlementSystem) | `modules/finance/system.py:L271` | ⚠️ **Movable** |
| 6 | Welfare & Wealth Tax | `government.run_welfare_check` | `provide_household_support`, `collect_tax` | `agents/government.py:L419` | ⚠️ **Movable** |
| 7 | Public Education | `government.run_public_education` | `settlement_system.transfer` | `systems/ministry_of_education.py:L30` | ⚠️ **Movable** |
| 8 | Infrastructure | `government.invest_infrastructure` | `withdraw` / `reflux_system.capture` | `agents/government.py:L472` | ⚠️ **Movable** |
| 9 | **Corporate Tax** | `tick_scheduler.py` (main loop) | `settlement_system.transfer` | `tick_scheduler.py:L377` | ❌ **Blocked** |

---

## Evaluation of Dependencies & Phase A Readiness

1.  **Dependency Analysis**:
    *   **Movable Transfers (Items 1-8)**: These transfers (Interest, Dividends, Welfare, etc.) are calculated based on the state at the beginning of the tick or after the matching phase. They do not depend on outcomes from later in the tick (like production). Therefore, their execution can be deferred. The logic can be changed to generate `Transaction` objects that are collected and passed to `_phase_transactions` for atomic execution.
    *   **Blocked Transfer (Item 9 - Corporate Tax)**: The corporate tax payment is critically blocked. It is calculated based on `firm.current_profit` (`tick_scheduler.py:L375`), which is determined by `firm.produce()` (`tick_scheduler.py:L371`). This production phase occurs *after* the entire Sacred Sequence, including `_phase_transactions`. Moving the tax payment into the transaction phase would require profit data that is not yet available, creating a circular dependency.

2.  **Phase A Sufficiency**:
    *   ✅ **Sufficient Groundwork**: The introduction of `FinanceDepartment`, `SettlementSystem`, and a dedicated `TransactionProcessor` shows that the necessary architectural components are in place. The system has moved away from scattered `agent.assets += ...` calls.
    *   ⚠️ **Incomplete Pattern Adoption**: Phase A stopped short of full normalization. Most new systems call `settlement_system.transfer` directly instead of creating and returning `Transaction` objects. The `process_profit_distribution` method in `FinanceDepartment` (`finance_department.py:L196-L215`), which correctly creates `Transaction` objects, is the ideal pattern that must be universally adopted.

## Proposed Implementation Path

To achieve 100% zero-sum integrity via a unified transaction phase, the following refactoring path is recommended.

### Track A: Convert "Movable" Transfers

Jules should convert all identified "Movable" items (1-8) into transaction-generating functions.

-   **Objective**: Modify each function (`bank.run_tick`, `firm.distribute_profit`, etc.) so that instead of calling `settlement_system.transfer` or `withdraw`/`deposit` directly, it creates and returns a `List[Transaction]`.
-   **Implementation**:
    1.  In `tick_scheduler.py`, create a new list, e.g., `system_transactions = []`.
    2.  Call each system function (e.g., `bank.run_tick`, `government.run_welfare_check`).
    3.  Extend `system_transactions` with the returned list of `Transaction` objects from each call.
    4.  Before `_phase_transactions` is called, extend `state.transactions` with `system_transactions`.
    5.  **Example**: `finance_department.py:L268`'s `distribute_profit_private` should not call `settlement_system.transfer`. It should create a `Transaction` for the dividend payment and return it in a list.

### Track B: Unblock and Convert Corporate Tax (Architectural Change)

This requires re-sequencing the main tick loop.

-   **Objective**: Make profit data available before the transaction phase.
-   **Proposed Change**:
    1.  In `tick_scheduler.py`, move the entire `for firm in state.firms:` loop responsible for production and needs updates (currently at `tick_scheduler.py:L369-L389`) to a new position *before* the Sacred Sequence begins (i.e., before `_phase_decisions` at `tick_scheduler.py:L274`).
    2.  This ensures that `firm.current_profit` is calculated based on the *previous* tick's state before any new decisions are made.
    3.  Once moved, the corporate tax calculation and payment logic can be converted into a transaction-generating function and integrated into Track A's workflow.

## Conclusion

The project is in a strong position to advance with WO-116 Phase B, but a simple migration is not possible. **Track A** can be implemented immediately to normalize the majority of asset transfers, significantly improving transactional integrity. However, completing the normalization requires the architectural change proposed in **Track B** to resolve the circular dependency related to corporate tax. Executing Track B first is recommended as it is the most invasive change, followed by the more straightforward conversions in Track A.
