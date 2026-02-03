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
    - `SettlementSystem`, `HousingSystem`, `Registry`, and `HousingTransactionHandler` updated to manipulate `liens` list instead of `mortgage_id`.
    - `SettlementSystem` now includes `loan_principal` and `lender_id` in transaction metadata to ensure `Registry` can accurately reconstruct Lien data.

## 3. Technical Debt & Insights

### 3.1. Type Hint Mismatch Resolved
The `RealEstateUnit.mortgage_id` type hint was `Optional[int]`, but the system consistently used string IDs (e.g., `"loan_123"`). This mismatch was corrected by defining `LienDTO.loan_id` as `str` and updating the `RealEstateUnit.mortgage_id` property return type to `Optional[str]`.

### 3.2. Redundant State Updates (Critical)
Both `SettlementSystem._transfer_property` and `Registry._handle_housing_registry` update the `RealEstateUnit` state.
- `SettlementSystem` updates it directly during execution.
- `Registry` updates it reactively when processing the transaction log.
**Risk**: If logic diverges, the state might be inconsistent depending on when it is read (pre- or post-Registry update). Currently, both are synchronized to update `liens`, but this duplication violates the Single Source of Truth principle.

### 3.3. Dependency Injection in Data Models
`RealEstateUnit` is a dataclass but now requires `IRealEstateRegistry` to function fully (`is_under_contract`). The current implementation uses an optional field `_registry_dependency` that defaults to `None`.
**Recommendation**: Move behavioral logic (checking contract status) out of the data model (`RealEstateUnit`) and into a Service (e.g., `HousingService` or `Registry`). Data models should ideally be anemic (pure state) in this architecture.

### 3.4. Unrelated Regression in Household/Lifecycle
During verification (`scripts/generate_golden_fixtures.py`), the simulation crashed at tick 19 with:
`AttributeError: 'Household' object has no attribute 'shares_owned'` in `simulation/systems/lifecycle_manager.py`.
This indicates that `Household` decomposition (moving shares to `portfolio`) has broken `LifecycleManager`, which still expects the old attribute. This prevented full fixture regeneration.

### 3.5. Transaction Metadata Quality
The `Transaction` model's `metadata` field is now critical for `Registry` to function correctly (reconstructing Liens). I added `loan_principal` and `lender_id` to the metadata in `SettlementSystem`. Future changes to Transaction structure must ensure these fields are preserved.
