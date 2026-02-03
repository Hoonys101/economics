# Housing V3 Saga Implementation Insights

## Mission: Atomic Housing Purchase via Settlement Saga

### Technical Debt Discovered
1.  **Mocking Fragility in Tests**:
    -   The `SettlementSystem` relies on `hasattr` checks to determine if an agent is a Firm (has `finance`) or Household (has `_econ_state`).
    -   `MagicMock` objects automatically create these attributes upon access, leading to incorrect logic paths (e.g., trying to compare a Mock object with a float).
    -   **Fix**: Used `spec` in `MagicMock` to strictly define available attributes.
    -   **Recommendation**: `SettlementSystem` should perhaps use stricter type checking (`isinstance`) or interface compliance rather than loose `hasattr` checks.

2.  **DTO Compatibility**:
    -   `MortgageApplicationDTO` existed in `housing_planner_api` with different field names (`property_value`, `principal`) compared to the new `housing_purchase_api` (`offer_price`, `loan_principal`).
    -   **Resolution**: Updated `LoanMarket` to support both formats via a compatibility layer, but a unification refactor is recommended.

3.  **Simulation State Access**:
    -   `HousingSystem.initiate_purchase` is called by `DecisionUnit` but needs access to `simulation.agents` to gather income data for the mortgage application.
    -   **Resolution**: Queued requests in `HousingSystem` and processed them in `process_housing` where `simulation` context is available. This introduces a slight delay (queued -> submitted) but preserves the architectural boundary.

### Architecture Alignment
-   **Saga Coordinator**: Successfully moved Saga coordination to `SettlementSystem` (Step 2 of plan), leveraging its existing atomic capabilities (`execute_multiparty_settlement`).
-   **Phase Integration**: Hooked `SettlementSystem.process_sagas` into `Phase3_Transaction` in `TickOrchestrator`, ensuring housing transactions occur alongside other financial activities.
-   **Macro-Prudential Regulations**: `LoanMarket` now strictly enforces LTV and DTI limits defined in `economy_params.yaml`.

### Manual Review Updates (Refactoring)
-   **HousingSystem**: Removed hardcoded `loan_term` and `existing_debt_payments`. Now fetches loan term from config and calculates existing debt payments by querying `Bank.get_debt_status`.
-   **LoanMarket**: Removed hardcoded `interest_rate` fallback. Refactored `stage_mortgage` to return `LoanInfoDTO` (dict) instead of just an ID, simplifying `apply_for_mortgage` and integrating staging logic more cleanly. Updated `ILoanMarket` interface in `housing_planner_api.py` to match.

### Verification
-   `scripts/verify_housing_transaction_integrity.py` confirms:
    -   Atomic transfer of Property, Loan Principal, and Down Payment.
    -   Strict T+1 separation between Loan Approval and Settlement.
    -   Correct rejection of loans exceeding DTI/LTV limits.
