# REF-001 Stateless Policy Engines: Implementation Insights

## Overview
This refactoring successfully extracted `FiscalEngine` and `MonetaryEngine` from `Government` and `CentralBank` agents, enforcing DTO-based communication and removing key abstraction leaks.

## Technical Debt & Trade-offs

1.  **Hardcoded Profit in Bailout Logic**:
    -   In `Government.provide_firm_bailout`, we construct `FirmFinancialsDTO` with `profit: 0.0` because accessing firm profit history requires deep inspection of the `firm` object (which we are trying to avoid leaking) or a new interface on `Firm`.
    -   **Impact**: Currently, `FiscalEngine` only checks `is_solvent` for bailouts, so this is benign. If future logic requires profit metrics, `Firm` must expose a DTO method like `get_financial_snapshot()`.

2.  **Shared DTO Definitions**:
    -   `MarketSnapshotDTO` is defined in `modules/finance/engines/api.py` and imported by `modules/government/engines/api.py`. Ideally, shared DTOs should be in a common `modules/system` or `modules/common` package to avoid coupling between `finance` and `government`.
    -   **Recommendation**: Move `MarketSnapshotDTO` to `modules/system/api.py` in a future refactor.

3.  **AI Policy Support**:
    -   The previous `GovernmentDecisionEngine` supported `AI_ADAPTIVE` mode via `AdaptiveGovBrain`. The new `FiscalEngine` currently only implements the Taylor Rule logic.
    -   **Status**: `AI_ADAPTIVE` is temporarily bypassed/simplified to Taylor Rule logic within the new Engine structure. The AI brain needs to be integrated into `FiscalEngine` or `FiscalEngine` needs to support strategy injection similar to how `GovernmentDecisionEngine` did, but strictly using DTOs.

4.  **Strategy Overrides in Monetary Engine**:
    -   `CentralBank` previously applied strategy overrides (scenarios) directly. We moved this logic into `MonetaryEngine` by passing optional override fields in `MonetaryStateDTO`.
    -   **Insight**: This keeps the engine stateless but leaks "scenario" concepts into the engine's input state. This is an acceptable trade-off for now to keep the engine pure.

## Verification
-   Unit tests for both engines verify core logic (Taylor Rule, Bailout eligibility).
-   Integration tests confirm `Government` agent correctly orchestrates the new `FiscalEngine`.
