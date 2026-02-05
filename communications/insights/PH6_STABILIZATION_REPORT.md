# Phase 6 Stabilization Report (PH6_BASELINE_STABILIZATION)

## 1. Executive Summary
This mission focused on finalizing the Phase 6 baseline by resolving a -71k monetary leak, hardening the engine against multi-currency crashes, and integrating persistence.
- **Status**: Partial Success. Crash fixed. Persistence added. Leak identified (Architectural) but not fully resolved (requires accounting model change).
- **Leak**: -71,328.04 (Steady). Identified as **Bank Profit Absorption**.

## 2. Resolved Technical Issues

### A. Engine Hardening (Multi-Currency Reset)
- **Problem**: `Phase5_PostSequence` attempted to assign a dictionary (`expenses_this_tick`) to a float field (`last_daily_expenses`), causing type errors and logic crashes in multi-currency scenarios.
- **Fix**: Implemented `FinanceDepartment.finalize_tick()` to encapsulate the reset logic.
- **Trade-off**: The fix calculates `last_daily_expenses` by **summing** raw values of all currencies (e.g. USD + EUR). This is a heuristic to prevent crashing and provide a rough magnitude for unit cost estimations. It ignores exchange rates as they are not readily available in the `PostSequence` context without heavy dependency injection.
- **Code**: `simulation/components/finance_department.py`, `simulation/orchestration/phases/post_sequence.py`.

### B. Persistence Integration
- **Problem**: Dashboard snapshots were not being saved to disk.
- **Fix**: Integrated `PersistenceBridge` into `DashboardService`. Snapshots are now saved at the end of `get_snapshot()`.
- **Code**: `simulation/orchestration/dashboard_service.py`.

### C. Settlement System Integrity
- **Problem**: Funds held in `SettlementSystem` (e.g. from deceased agents) were invisible to the M2 calculation, creating potential leaks.
- **Fix**: Implemented `get_assets_by_currency` in `SettlementSystem` and added it to `TickOrchestrator`'s `currency_holders`.
- **Code**: `simulation/systems/settlement_system.py`, `simulation/orchestration/tick_orchestrator.py`.

## 3. Residual Leak Analysis (-71,328.04)

The simulation consistently reports a leak of **-71,328.04** at Tick 1.

### Root Cause: Bank Profit Absorption
The M2 Money Supply formula used in the simulation is:
`M2 = (M0 - Bank Reserves) + Deposits`

When agents pay **interest** to the Commercial Bank:
1.  **Agent Cash** decreases (reducing `M0` and `M2`).
2.  **Bank Reserves** increase (increasing `M0` but subtracted from `M2`).
3.  **Bank Equity** increases (Profit).
4.  **Deposits** do *not* increase (it is not a deposit, it is income).

**Result**: Net reduction in M2.

The `Authorized Delta` (Expected M2) calculation only tracks `Central Bank Issuance` vs `Destruction`. It does **not** account for money removed from circulation via Bank Profit Retention.
Since the Bank has not yet paid out dividends or expenses equal to this income at Tick 1, the money is effectively "hoarded" in Reserves, causing the M2 drop.

### Central Bank Activity
The logs show `CentralBank` delta of **-3.8M**. This is likely **Quantitative Easing (QE)** or Open Market Operations where the CB buys Bonds from the Commercial Bank.
- **Mechanism**: CB buys Bonds -> Bank Reserves increase.
- **M2 Impact**: `M0` increases (Reserves), but `Reserves` deduction increases. `M2` remains neutral.
- **Conclusion**: The large CB delta is an asset swap and is **not** the source of the leak.

### Recommendation
To resolve the leak metric:
1.  **Accounting Adjustment**: Update `Authorized Delta` to include `Bank Retained Earnings` as a form of "Temporary Destruction" (Absorption).
2.  **Operational Adjustment**: Force the Bank to distribute all profits (Dividends/Salaries) within the same tick to recycle liquidity.
3.  **Acceptance**: Accept this as a feature of the M2 definition (Hoarding reduces Money Supply).

## 4. Technical Debt & Next Steps
- **FinanceDepartment.finalize_tick**: Need to inject `ExchangeService` to properly convert expenses for `last_daily_expenses`.
- **Bank Accounting**: The current M2 check is too rigid for a fractional reserve system where Bank Equity fluctuates.
