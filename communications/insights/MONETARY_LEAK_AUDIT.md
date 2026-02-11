# Report: Analysis of Money Leak from Infrastructure Spending

## Executive Summary
A money leak of precisely 5,000.00 is occurring each tick due to infrastructure spending. The root cause is an orchestration issue: money created from government bond sales to fund these projects is not being registered with the `MonetaryLedger`, causing a discrepancy between the actual money supply and the officially recorded (authorized) money supply.

## Detailed Analysis

### 1. Leak Identification
- **Status**: ✅ Confirmed
- **Evidence**: `leak.txt`
  - The trace script reports a final `Actual Delta` of `+5,000.00`.
  - The `Authorized Delta` calculated from the `MonetaryLedger` is `0.00`.
  - This results in a reported `❌ LEAK DETECTED: 5,000.0000`.
  - The log explicitly identifies `Detected Infrastructure Spending: 5,000.00`, linking the leak to this activity.

### 2. Money Creation Flow (Infrastructure)
- **Status**: ✅ Implemented
- **Evidence**: `modules/government/components/infrastructure_manager.py`
- **Notes**:
    1.  The `InfrastructureManager.invest_infrastructure` function is called to initiate public works projects (`L14`).
    2.  If the government lacks funds, it issues bonds to raise the necessary capital (`L32-L38`). The `issue_treasury_bonds_synchronous` method is expected to handle the creation of new money and return corresponding `Transaction` objects (e.g., of type `bond_purchase`).
    3.  The manager then creates `infrastructure_spending` transactions to pay households, which are correctly logged (`L65-L78`).

### 3. Monetary Ledger Registration Flow
- **Status**: ✅ Implemented (but improperly used)
- **Evidence**: `modules/government/components/monetary_ledger.py`, `simulation/agents/government.py`
- **Notes**:
    1.  The `MonetaryLedger` is designed to track the money supply. Its `process_transactions` method identifies monetary expansion/contraction events (`monetary_ledger.py:L33`).
    2.  Specifically, it is programmed to recognize `bond_purchase` by the central bank as monetary expansion (`monetary_ledger.py:L52-L58`).
    3.  The `Government` agent provides an interface, `process_monetary_transactions`, to pass all tick-related transactions to the ledger (`government.py:L263`).

### 4. Root Cause: Missing Registration Call in Orchestrator
- **Status**: ❌ Missing
- **Evidence**: Inferred from `leak.txt` and code structure.
- **Diagnosis**: The `trace_leak.py` script confirms that `credit_destruction` events are correctly processed by the `MonetaryLedger`, indicating that `government.process_monetary_transactions` *is* being called at some point. However, the money created to fund infrastructure is not being tracked.

This leads to the following conclusion: The simulation's central orchestrator (the main loop in `run_tick`) calls `government.invest_infrastructure` and collects the resulting transactions. However, it fails to subsequently pass this list of transactions to `government.process_monetary_transactions`. The call to register monetary events is either happening *before* the infrastructure transactions are generated or the orchestrator is simply omitting them from the call. This is the "missing registration call" that prevents the ledger from accounting for the new money from the bond sale.

## Conclusion
The leak is not in the `InfrastructureManager` or the `MonetaryLedger` themselves, but in the overarching simulation loop that orchestrates their operations. To fix this, the orchestrator must be modified to ensure that **after all transactions for a tick are generated and collected (including those from bond sales for infrastructure), a comprehensive call is made to `government.process_monetary_transactions` with the complete list.** This will ensure all monetary creation events are registered and eliminate the leak.
