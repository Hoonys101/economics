# TD-Fix-AB-Failures: Fixing Category A and B Test Failures

## Phenomenon
Multiple integration tests were failing due to outdated test setups and DTO mismatches.
- `test_bank_deposit_balance` failed because `Bank.__init__` requires `config_manager`.
- `test_process_omo_purchase_transaction` failed because `MockAgent` lacked `_econ_state`.
- `test_standalone_firm_engine_uses_dto` failed because `FirmStateDTO` now uses nested DTOs (Composite State) but the test was passing flat arguments.
- `test_household_attributes_initialization` failed because `Household` properties `gender` and `home_quality_score` were moved to sub-components (`_bio_state`, `_econ_state`) and not exposed.

## Cause
- **Refactoring Drift**: The core codebases (`Bank`, `FirmStateDTO`, `Household`) were refactored (e.g., Household Refactor Stage B, Firm Composite State), but the integration tests were not updated to reflect these architectural changes.
- **DTO Evolution**: `FirmStateDTO` evolved to a composite structure, breaking tests that assumed a flat structure.
- **Missing Facade Properties**: `Household` removed property delegates for `gender` and `home_quality_score` which some tests and consumers still expected.

## Solution
1.  **Update Test Mocks**: Provide `config_manager` to `Bank` in tests.
2.  **Update Mock Objects**: Add `_econ_state` to `MockAgent` to mimic `BaseAgent` structure.
3.  **Update DTO Usage**: Update `test_standalone_firm_engine_uses_dto` to construct nested department DTOs before creating `FirmStateDTO`.
4.  **Restore Facade Properties**: Add `@property` delegates to `Household` for `gender` and `home_quality_score` to maintain backward compatibility and ease of access.

## Lesson Learned
- **Integration Test Maintenance**: Integration tests are sensitive to interface changes. When refactoring core agents or DTOs, `grep` should be used to find all test usages, not just unit tests.
- **DTO Versioning**: When significantly changing DTO structure (flat to nested), consider a factory method or backward-compatible init if possible, or enforce strict updates across the board immediately.
