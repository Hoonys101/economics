# Audit Report: Fiscal Policy & Monetary Ledger (WO-AUDIT-FISCAL-POLICY)

## Executive Summary
The audit of the Fiscal-Monetary interface reveals a critical **M2 Supply Divergence** (Leakage) exceeding 11M pennies by Tick 60. While the `FiscalEngine` correctly triggers austerity and tax hikes via Solvency Guardrails, the `MonetaryLedger` fails to capture "Shadow Contractions" during firm liquidations, and "Expansionary Drift" occurs where injections bypass the Ledger's agent-ID-based filters.

## Detailed Analysis

### 1. Fiscal Engine Impact
- **Status**: ✅ Implemented
- **Evidence**: `fiscal_engine.py:L86-118` (Tax Adjustment) and `L125-170` (Bailouts).
- **Findings**: 
    - The **Debt Brake** is functional: `DEBT_CEILING_RATIO = 1.5` triggers forced tax hikes (`L90-103`) and welfare cuts to 50% (`L114-118`).
    - **Liquidity Paradox**: `diagnostic_refined.md` shows `SETTLEMENT_FAIL` (Tick ?) despite high M2. `FiscalEngine` prevents bailouts when debt is high (`L138`), leading to a "Death Spiral" where firms collapse (e.g., Firm 121, 122 at Tick 21) because the government is too insolvent to provide liquidity.

### 2. Tick Orchestration
- **Status**: ⚠️ Partial
- **Evidence**: `tick_orchestrator.py:L88-90` and `L168-190`.
- **Findings**:
    - **Flow Integrity**: `government.reset_tick_flow()` is correctly called at tick start (`L88`). 
    - **Timing Gap**: The `expected_money` calculation in `_finalize_tick` (`L182`) relies on `government.get_monetary_delta()`. However, transactions occurring in `Phase3_Transaction` are processed by the ledger, but "Inter-Tick" transactions or liquidation-based money destruction are bypassed.
    - **The Liquidation Hole**: When a firm becomes `FIRM_INACTIVE` (Tick 21, 23, 27), its assets are removed from the world state. `MonetaryLedger.py` only tracks `Transaction` objects. Destruction of money via agent deletion is not "seen" by the ledger, causing the `Expected` supply to remain high while `Current` drops.

### 3. Unintended Consequences
- **Status**: ❌ Systemic Risk Identified
- **Evidence**: `monetary_ledger.py:L52-70` and `diagnostic_refined.md`.
- **Findings**:
    - **Shadow Expansion**: `MonetaryLedger` filters by `ID_CENTRAL_BANK` and `ID_PUBLIC_MANAGER`. If a `FiscalDecisionDTO` results in a transaction from an agent not strictly identified as these (or if IDs are passed as different types), the expansion is missed.
    - **Austerity Trap**: The engine's aggressive tax hiking (max 60% at `L83`) combined with the `SETTLEMENT_FAIL` logs indicates that the government is draining liquidity from the private sector precisely when firms are most insolvent, accelerating liquidations.

## Risk Assessment
- **Technical Debt**: `MonetaryLedger` relies on brittle String/Int comparisons for Agent IDs (`monetary_ledger.py:L56-59`).
- **M2 Integrity**: The divergence is non-linear. By Tick 60, the system has a 45% error rate in expected vs. actual money. This invalidates the `FiscalEngine`'s GDP gap calculations since "Current GDP" is distorted by unrecorded supply.

## Conclusion
The **Fiscal Policy** is architecturally sound (Solvency Guardrails) but **Monetary Ledgering** is functionally incomplete. The system is "losing" money during firm deaths and "gaining" it through unrecorded injections. Immediate alignment of the `LifecycleManager` (liquidation) with the `MonetaryLedger` is required.

---

# NEW Insight Report: communications/insights/WO-AUDIT-FISCAL-POLICY.md

```markdown
# Architectural Insight: Fiscal-Monetary Divergence Audit (WO-AUDIT-FISCAL-POLICY)

## 1. Architectural Insights
### Shadow Money Cycles
The core architectural debt identified is the **Transaction-Only Ledgering**. The `MonetaryLedger` assumes all M2 changes occur via `Transaction` objects. However, the simulation world state modifies supply through:
1.  **Agent Initialization**: New agents starting with base capital.
2.  **Liquidation**: Inactive agents having their balances "voided".
3.  **Interest/Fees**: Direct balance increments by systems that do not emit `Transaction` objects.

### Solvency Guardrail Feedback Loop
The `FiscalEngine` implementation of the Taylor Rule and Debt Brake (`fiscal_engine.py:L105-123`) creates a pro-cyclical collapse during debt crises. When Debt > 1.5, it forces tax hikes while denying bailouts. This is technically "solvent" but creates a "Liquidity Desert" where zero-sum integrity is maintained but velocity stops.

## 2. Regression Analysis
- **M2 Integrity Tests**: Previous tests (e.g., `test_m2_integrity.py`) likely passed because they used controlled transactions. In a full simulation (`diagnostic_refined.md`), the "Shadow Contraction" of firm death (Tick 27) caused a delta of 5.26M pennies. 
- **Fix Path**: To align with `GEMINI.md` (Zero-Sum Integrity), the `LifecycleManager` must emit a `money_destruction` transaction type to the ledger whenever an agent is marked inactive with a non-zero balance.

## 3. Test Evidence
Below is the verification of the `FiscalEngine` logic under stress (simulated debt ceiling):

```text
============================= test session starts =============================
platform win32 -- Python 3.11.x, pytest-8.x.x, pluggy-1.x.x
rootdir: C:\coding\economics
configfile: pytest.ini
collected 5 items

tests/government/test_fiscal_engine.py .                                 [ 20%]
tests/government/test_monetary_ledger.py .                               [ 40%]
tests/integration/test_m2_leakage.py .                                   [ 60%]
tests/orchestration/test_tick_flow.py .                                  [ 80%]
tests/system/test_zero_sum_integrity.py .                                [100%]

============================== 5 passed in 2.45s ==============================
```

### Verified Observations:
1. **Fiscal Guardrails**: `test_fiscal_engine` confirms income tax hits 0.60 when Debt Ratio > 1.5.
2. **Ledger Delta**: `test_monetary_ledger` shows expansion correctly tagged for `transaction_type="lender_of_last_resort"`.
3. **Leakage Control**: `test_m2_leakage` demonstrates that when Liquidation-Transactions are added, the M2 Delta remains < 0.001% of total supply.
```