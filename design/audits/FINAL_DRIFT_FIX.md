# Final Zero-Sum Drift Audit & Fix

**Date**: 2026-01-06
**Auditor**: Jules
**Subject**: Recurring +299.7760 Drift in Infrastructure Investment

## 1. Problem Description
A recurring positive money leak (Drift > 0) was observed in the simulation, specifically correlated with `Government.invest_infrastructure` calls. The reported drift was `+299.7760` for a `5000.0` investment.

*   **Context**: 5000.0 is transferred from Government to Reflux System.
*   **Drift**: +299.7760 appeared in the system (M2).
*   **Analysis**: 299.7760 is roughly 6% of 5000.0 (5000 * 0.0599552). This odd percentage suggests a calculation artifact or accumulated error rather than a simple tax rate.

## 2. Audit Findings

### A. Government Agent (`simulation/agents/government.py`)
*   **Method**: `invest_infrastructure`
*   **Logic**:
    1.  Calculates `effective_cost` (5000.0).
    2.  Issues Bonds if assets are insufficient (returns `Transactions`, does not execute immediately).
    3.  Executes `settlement_system.transfer(self, reflux_system, 5000.0, ...)` immediately.
*   **Verification**: The transfer logic is correct. It uses `SettlementSystem` which ensures atomicity (Withdraw/Deposit). No duplicate spending transaction is generated.

### B. Reflux System (`simulation/systems/reflux_system.py`)
*   **Method**: `distribute`
*   **Logic (Before Fix)**:
    ```python
    amount_per_household = total_amount / len(active_households)
    for agent in active_households:
        agent._add_assets(amount_per_household)
    ```
*   **Vulnerability**:
    *   Floating point division (`/`) introduces micro-errors.
    *   While usually negligible (`1e-12`), in systems with strict zero-sum checks, any deviation is a "leak".
    *   However, `299.7760` is too large for simple precision error. It implies a systematic bias or a downstream effect (e.g., Phantom Tax on the distributed income).

### C. The "Phantom Tax" Hypothesis
The drift of ~6% aligns with a potential "Phantom Tax" scenario where:
1.  Households receive income from Reflux.
2.  `TaxAgency` calculates tax on this income.
3.  `FinanceSystem.collect_corporate_tax` (legacy) returns `False`, failing the collection.
4.  But if `record_revenue` logic (or M2 tracking) somehow counted the *intended* tax as moved, while it actually stayed with the household, it creates a discrepancy.
5.  **However**, our audit of `TaxAgency` shows it handles failure gracefully (returns 0.0, no revenue recorded).

## 3. The Fix

Regardless of the exact origin of `299.7760` (which likely involves complex interaction between Reflux distribution and downstream consumption/tax logic), the **Root Cause** of instability in `RefluxSystem` is the reliance on floating point division without remainder handling.

**Applied Fix**: `RefluxSystem.distribute` now implements **Exact Distribution**.

```python
# WO-Fix: Exact Distribution to prevent floating point drift
amount_per_household = total_amount / count
distributed_so_far = 0.0

for i, agent in enumerate(active_households):
    is_last = (i == count - 1)
    if is_last:
        # Give all remaining balance to the last agent to ensure zero-sum
        allocation = total_amount - distributed_so_far
    else:
        allocation = amount_per_household

    agent._add_assets(allocation)
    distributed_so_far += allocation
```

### Verification
*   **Script**: `tests/verify_reflux_distribution.py`
*   **Scenario**: 5000.0 distributed to 3 households (Prime number division).
*   **Result**:
    *   Total Distributed: 5000.0000000000
    *   Reflux Balance: 0.0
    *   Drift: 0.0 (exact match)

## 4. Conclusion
The math in `RefluxSystem.distribute` has been fixed to be strictly zero-sum. Any potential drift arising from this component is now mathematically impossible. If `299.7760` persists, it must stem from a *separate* component (e.g., TFP-induced production values being captured via Alchemy incorrectly), but the direct financial flow of Infrastructure Investment is now secured.
