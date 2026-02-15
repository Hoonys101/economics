# Report: Analysis of Money Leak in Infrastructure Spending

## Executive Summary
The detected money leak of `5,000.00` is caused by a missing "registration" step in the simulation's orchestration logic. The `InfrastructureManager` correctly generates `bond_purchase` transactions to fund spending, but these transactions are not being passed to the `MonetaryLedger` for tracking. Consequently, the authorized monetary expansion is not recorded, creating a discrepancy between the actual money supply and the accounted-for total.

## Detailed Analysis

### 1. Infrastructure Funding and Transaction Generation
- **Status**: ✅ Implemented
- **Evidence**: `modules/government/components/infrastructure_manager.py:L39-L53`
- **Notes**: When the `Government` lacks funds for infrastructure, the `InfrastructureManager.invest_infrastructure` method correctly triggers the finance system to issue bonds. The resulting bond transactions (`bond_txs`) are appended to a list of transactions that is returned to the caller. This process correctly models the creation of new money when the Central Bank purchases these bonds.

### 2. Monetary Ledger's Tracking Capability
- **Status**: ✅ Implemented
- **Evidence**: `modules/government/components/monetary_ledger.py:L57-L63`
- **Notes**: The `MonetaryLedger.process_transactions` method is designed to identify monetary expansion. It correctly checks for `transaction_type` equal to `bond_purchase` and verifies if the buyer is the `ID_CENTRAL_BANK`. If these conditions are met, the transaction's value is added to the `credit_delta_this_tick`, correctly accounting for the new money.

### 3. The Missing Registration Step
- **Status**: ❌ Missing
- **Evidence**: `leak.txt:L1,L17,L45-L48`, `scripts/trace_leak.py:L40-L42`
- **Notes**:
    - The log (`leak.txt`) shows that the `Actual Delta` in system money is `5,000.00`, while the `Authorized Delta` (as tracked by `MonetaryLedger`) is `0.00`, resulting in the `5,000.00` leak.
    - The log also shows `infrastructure_spending` transactions but conspicuously omits the `bond_purchase` transactions that must have occurred to fund them.
    - The `trace_leak.py` script demonstrates the correct pattern for a manually created loan: the resulting `credit_tx` is immediately passed to `sim.government.process_monetary_transactions`.
    - The issue is that the simulation's orchestrator, after calling `Government.invest_infrastructure` and receiving the list of transactions (containing the crucial `bond_purchase` transaction), fails to subsequently pass this list to `Government.process_monetary_transactions`. This omission means the `MonetaryLedger` is never aware of the monetary expansion event.

## Risk Assessment
The current implementation flaw breaks the simulation's zero-sum integrity for monetary events. Any government spending funded by Central Bank bond purchases will be incorrectly flagged as a money leak, undermining the accuracy of economic diagnostics and potentially leading to incorrect simulation outcomes.

## Conclusion
The root cause is not within the `InfrastructureManager` or `MonetaryLedger` but in the higher-level orchestrator code that calls them. The orchestrator must be modified to take the transactions returned by `Government.invest_infrastructure` and immediately pass them to `Government.process_monetary_transactions` to ensure all monetary events are correctly registered.