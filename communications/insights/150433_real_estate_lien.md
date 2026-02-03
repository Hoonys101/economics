# Mission 150433: RealEstateUnit Lien Data Structure Implementation

## 1. Overview
This mission implemented the `Lien` data structure in `RealEstateUnit`, replacing the single `mortgage_id` field with a list of `LienDTO` objects. This supports multiple encumbrances (mortgages, tax liens, judgments) and provides a more robust foundation for the financial simulation.

## 2. Key Changes
- **`RealEstateUnit` Schema**:
    - Added `liens: List[LienDTO]`.
    - Removed `mortgage_id` field.
    - Added `mortgage_id` read-only property for backward compatibility (returns the first mortgage's loan ID).
    - Added `is_under_contract` property delegating to `IRealEstateRegistry`.
    - Added `_registry_dependency` for the above delegation.
- **DTO Centralization**:
    - `LienDTO`, `MortgageApplicationDTO` defined in `modules/finance/api.py`.
    - `modules/market/housing_planner_api.py` and `modules/housing/dtos.py` now import `MortgageApplicationDTO` from `finance/api.py`.
- **Logic Updates**:
    - `SettlementSystem` now triggers state updates via Transaction logging (metadata: `mortgage_id`, `loan_principal`, `lender_id`) rather than direct mutation, making `Registry` the single source of truth.
    - `Registry._handle_housing_registry` logic updated to reconstruct `liens` from transaction metadata.
    - `HousingSystem` and `HousingTransactionHandler` updated to manipulate `liens` list.
- **Regression Fixes**:
    - Fixed `LifecycleManager` regression by replacing deprecated `agent.shares_owned` with `agent.portfolio.holdings`.
    - Fixed `verify_mortgage_pipeline_integrity.py` mock configuration for regulatory checks.

## 3. Technical Debt & Insights

### 3.1. Type Hint Mismatch Resolved
The `RealEstateUnit.mortgage_id` type hint was `Optional[int]`, but the system consistently used string IDs (e.g., `"loan_123"`). This mismatch was corrected by defining `LienDTO.loan_id` as `str` and updating the `RealEstateUnit.mortgage_id` property return type to `Optional[str]`.

### 3.2. Single Source of Truth Enforced
Previously, `SettlementSystem` and `Registry` both updated `RealEstateUnit` state, risking divergence. The `SettlementSystem._transfer_property` method was refactored to `_log_property_transfer`, which creates a Transaction with rich metadata. The `Registry` is now the sole authority for updating ownership and liens based on these transactions.

### 3.3. Dependency Injection in Data Models
`RealEstateUnit` is a dataclass but now requires `IRealEstateRegistry` to function fully (`is_under_contract`). The current implementation uses an optional field `_registry_dependency` that defaults to `None`.
**Recommendation**: Move behavioral logic (checking contract status) out of the data model (`RealEstateUnit`) and into a Service (e.g., `HousingService` or `Registry`). Data models should ideally be anemic (pure state) in this architecture.

### 3.4. Transaction Metadata as Protocol
The `Transaction` model's `metadata` field is now critical for `Registry` to function correctly (reconstructing Liens). The fields `loan_principal` and `lender_id` must be preserved in any future transaction schema changes.

### 3.5. Simulation Stability
The `LifecycleManager` fix (using `portfolio`) restored simulation stability, allowing successful generation of golden fixtures up to tick 100. This highlights the importance of comprehensive regression testing when refactoring core agent attributes.
