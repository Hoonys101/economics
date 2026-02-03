# Insight Report: H1-Housing-V2 (The Great Housewarming)

## Mission Summary
Implemented the modernization of the housing credit pipeline, enforcing atomic transactions, macro-prudential regulations (LTV/DTI), and a new bubble monitoring system.

## Technical Debt & Issues

### 1. DTO Completeness & Fragmentation
- **Issue**: `HouseholdStateDTO` lacks critical financial fields like `liabilities`, `current_debt`, or `annual_income`.
- **Impact**: `HousingPlanner` requires these fields for DTI calculations.
- **Workaround**: Extended `HousingOfferRequestDTO` to include `applicant_current_debt` and `applicant_annual_income`.
- **Recommendation**: Update `HouseholdStateDTO` to include a comprehensive financial summary (Assets, Liabilities, Income, Expenses).

### 2. Loan ID Consistency
- **Issue**: `LoanMarket` and `HousingPlanner` often treat Loan IDs as integers, while `Bank` uses string keys (e.g., `"loan_123"`).
- **Impact**: Potential `KeyError` or mismatch when voiding loans or querying status.
- **Workaround**: Implemented heuristic matching (splitting strings, hashing) in `SagaHandler` and `LoanMarket`.
- **Recommendation**: Standardize Loan IDs across the system (preferably UUID or consistent Integer).

### 3. Configuration Management Testability
- **Issue**: `ConfigManager` is tightly coupled to the file system and hard to mock in isolation without dependency injection.
- **Impact**: Verification scripts required hacking `MagicMock` or manual `ConfigManager` instantiation.
- **Recommendation**: Refactor `ConfigManager` to be easily mockable or provide a `TestConfigManager`.

### 4. Integration of HousingPlanner
- **Issue**: `HousingPlanner` (stateless) has been implemented, but the legacy `HousingManager` (stateful) might still be in use by `SocialSystem` or `AIDrivenHouseholdEngine`.
- **Impact**: Dual logic paths might exist temporarily.
- **Recommendation**: Deprecate `HousingManager` and wire all decision engines to use `HousingPlanner`.

### 5. Bank "Reserves" vs Credit Creation
- **Issue**: The atomic settlement spec required "Debit Bank Reserves". This implies a Full Reserve or "Lending from Equity" model for the settlement step, whereas `Bank.grant_loan` follows Fractional Reserve/Credit Creation (Asset/Liability expansion).
- **Impact**: To satisfy the spec's atomic transfer requirement, `Bank` effectively "lends cash" in the `SettlementSystem` step.
- **Resolution**: Implemented `stage_loan` (creates Asset, no Liability) + `SettlementSystem` transfer (Bank Cash -> Borrower -> Seller). This maintains accounting integrity but effectively models "Cash Lending" for the transaction duration.

## Verification
- `scripts/verify_mortgage_pipeline_integrity.py`: Passed. Confirmed atomic transfer, loan staging, and rollback on failure.
- `scripts/verify_bubble_observatory.py`: Passed. Confirmed metric collection and logging.
