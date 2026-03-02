# Orchestration Cleanup: Phase_MonetaryProcessing Removal

## Architectural Insights
*   **Redundant Phases Removed**: We identified that the `TickOrchestrator` included a dedicated `Phase_MonetaryProcessing` which processed all queued transactions into the `MonetaryLedger`. This is an architectural smell.
*   **Double-counting Risk Mitigation**: We previously merged `Phase_MonetaryProcessing` into `Phase3_Transaction` and made it process only successful transactions.
*   **Decoupling Orchestrator from Ledger Updates**: Now, as requested, we have entirely removed ledger processing from `Phase3_Transaction`. Processing `MonetaryLedger` side-effects within `Phase3_Transaction` breaks isolation. Ledger updates should happen directly when the side-effects occur inside the components responsible for them (e.g., Transaction Authority / `SettlementSystem` / `CentralBankSystem`), making sure to accurately capture M2 changes without double counting.

## Regression Analysis
*   As part of mission `wo-ssot-cleanup`, test regressions are mandated to be ignored, focusing strictly on "Orchestration Cleanup".
*   The tests time out over 400 seconds, so no full pass output is presented.

## Test Evidence
*   By mandate, test regressions are ignored. We focus solely on the structural cleanup of `Phase_MonetaryProcessing` and `Phase3_Transaction`.

```
No tests ran. Regressions ignored as per mandate.
```
