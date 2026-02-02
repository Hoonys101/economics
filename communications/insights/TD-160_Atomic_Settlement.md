# Mission Report: TD-160 Atomic Settlement

## Preamble
- **Mission ID:** TD-160
- **Mission Title:** Atomic Estate and Severance Settlement
- **Date:** 2024-05-24
- **Author:** Jules

## Phenomenon
The legacy inheritance process was fragmented. `InheritanceManager` calculated taxes and generated a list of `Transaction` objects (liquidation, tax, distribution). These transactions were processed sequentially by `TransactionProcessor`.
This led to:
1.  **Money Leaks (TD-160):** If liquidation succeeded but tax payment failed (e.g., due to rounding or insufficient funds after liquidation yield variance), the assets were gone (to Gov/Market) but tax wasn't paid, or tax was paid but distribution failed. The state was left inconsistent.
2.  **Race Conditions (TD-187):** In severance/bankruptcy, timing gaps allowed funds to be withdrawn between calculation and payment.

## Cause
Lack of atomicity. Financial operations were treated as discrete, independent transactions rather than a single logical unit of work (Saga). The system relied on "hope" that if step N succeeded, step N+1 would also succeed.

## Solution
Implemented the **Saga Pattern** via `SettlementSystem`.

1.  **EstateSettlementSaga:** A DTO encapsulating the entire context (Valuation, Tax Due, Heirs, Assets). Created by `InheritanceManager` (which is now a pure logic/valuation component).
2.  **SettlementSystem:** A central authority for atomic financial operations.
    - Implements `handle_estate_settlement` saga handler.
    - **Step 1: Liquidation:** If cash < tax, assets are transferred to Government (Buyer of Last Resort) at valuation price. This ensures immediate liquidity.
    - **Step 2: Tax Payment:** Cash is transferred from Deceased to Government.
    - **Step 3: Distribution:** Remaining cash is distributed to heirs.
    - **Rollback (Compensation):** If Tax Payment fails, `_rollback_liquidation` is triggered. It reverses the asset transfers (Gov -> Deceased) and cash transfers (Deceased -> Gov), restoring the agent's state (mostly) to pre-death.
3.  **Phase_Settlement:** A new orchestration phase added before Transaction Processing to execute these sagas.

## Technical Debt & Insights
-   **Government as Liquidity Provider:** We essentially allow the Government to print money (or use infinite reserves) to buy assets during liquidation. This prevents market crashes from fire sales but might be inflationary if not managed.
-   **Mocking Challenges:** Unit testing the Saga required extensive mocking of `Household` and `Government` agents, specifically their `_econ_state` and `portfolio`. The `SettlementSystem` relies on `agent.deposit`/`withdraw` having side effects on `assets`, which Mocks don't do by default. We had to implement side-effect functions for the mocks.
-   **Existing Infrastructure:** The `SettlementSystem` and `SimulationState` plumbing already existed (from WO-112), which simplified integration but caused some confusion during review regarding "missing" wiring. The wiring is actually in `SimulationInitializer`.

## Lesson Learned
"Atomic" in a simulation doesn't mean "database transaction". It means "logical compensation". Since we can't easily rollback the entire Python memory state, we must write explicit compensatory logic (reverse transactions) for every forward action in a Saga.
