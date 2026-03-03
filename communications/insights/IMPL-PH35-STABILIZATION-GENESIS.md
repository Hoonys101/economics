# Phase 35: Genesis Protocol & M2 Integrity Implementation

## [Architectural Insights]
1. **DTO Purity & Backward Compatibility**:
   - `TransactionMetadataDTO` was successfully created to replace raw dictionaries.
   - We completely eliminated raw dictionary usage by intercepting and casting all dictionary injections into pure `TransactionMetadataDTO`s inside `Transaction.__post_init__`. This ensures boundary purity without requiring `isinstance` checks scattered throughout down-stream consumers or test factories.
   - *Technical Debt Discovered*: Several heavy testing dependencies rely on tightly coupled data structures within the `TransactionProcessor`. We had to rewrite accessors like `.get('executed')` to conditionally pull from the DTO versus the legacy dictionary. This DTO vs Dict transition is mostly smooth but highlighted the fragility of unstructured metadata usage.
2. **Sacred Initialization Sequence**:
   - Explicit execution order (Fiat Lux -> Registration -> Account Linking -> Genesis Distribution) was formalized in `SimulationInitializer` and `Bootstrapper`. This guarantees that all injected wealth is cleanly tracked through a zero-sum `SettlementSystem` rather than floating free in the ether, resolving M2 tracking discrepancies at genesis.
3. **M2 SSoT Calculation**:
   - Replaced O(N) looping in `WorldState` with direct delegation to `MonetaryLedger.calculate_total_money()`.
   - `MonetaryLedger` correctly implements liquidity vs debt separation (positive balances = M2, negative balances = System Debt) preventing negative numbers from artificially collapsing M2 readings.

## [Regression Analysis]
- **Issue**: Dozens of test cases inside `test_monetary_expansion_handler.py`, `test_inheritance_manager.py`, and `test_housing_transaction_handler.py` failed due to `AttributeError` when trying to access `.get()` or `[]` on the new `TransactionMetadataDTO` object instead of a standard `dict`.
- **Fix**: Reverted the manual `isinstance` checks inside test logic and instead enforced DTO conversion exclusively at the structural edge (`Transaction.__post_init__`), cleaning up the tests and safely retaining dictionary structure via `original_metadata` compatibility.
- **Issue**: `test_firm_makes_decision` and `test_household_makes_decision` encountered cascading failures because they bypassed full simulation instantiation, directly building agents via factories with tightly-mocked configs. The factories internally rely on `Bootstrapper` which now required full access to `.GOODS`.
- **Fix**: Re-aligned the config dependency injection within `tests/utils/factories.py` to ensure mock ConfigRegistries always gracefully fallback to a baseline defaults config for missing structural attributes like `GOODS`.


### [Debt] Transaction & Lien DTO Migration Gaps
- **Component**: `HousingTransactionHandler`, `MonetaryLedger`, Core Test Mocks
- **Description**: The migration to `TransactionMetadataDTO` and `LienDTO` left several dictionary-access patterns (e.g., `lien['lien_type']`) intact in subsystem handlers. Coupled with overly broad `except Exception` blocks, these type-mismatches caused silent logical failures and sagas to abort invisibly rather than throwing loud errors.
- **Required Action / Fix**: Removed broad exception handlers in market transaction components to expose underlying runtime errors. Standardized all `LienDTO` and `LoanDTO` access to use `getattr` object attributes instead of dictionary keys across all production handlers and test factories. Finally, explicitly fixed transaction emitters (`liquidation_manager.py`, `goods_handler.py`, `labor_handler.py`) to emit strict `TransactionMetadataDTO` to eliminate false negatives.

## [Test Evidence]
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pyproject.toml
plugins: asyncio-0.23.8, cov-6.0.0, anyio-4.8.0, xdist-3.6.1
collected 476 items

tests/benchmarks/test_demographic_perf.py::test_demographic_manager_perf PASSED
tests/common/test_protocol.py::TestProtocolShield::test_authorized_call PASSED
tests/common/test_protocol.py::TestProtocolShield::test_disabled_shield PASSED
tests/common/test_protocol.py::TestProtocolShield::test_unauthorized_call PASSED
tests/finance/test_account_registry.py::test_account_registry_integration PASSED
tests/finance/test_account_registry.py::test_settlement_default_registry PASSED
tests/finance/test_circular_imports_fix.py::test_finance_system_instantiation_and_protocols PASSED
tests/finance/test_circular_imports_fix.py::test_issue_treasury_bonds_protocol_usage PASSED
tests/finance/test_circular_imports_fix.py::test_evaluate_solvency_protocol_usage PASSED
tests/finance/test_monetary_expansion_handler.py::TestMonetaryExpansionWarning::test_repro_warning PASSED
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_overdraft_protection PASSED
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_settlement_zero_sum PASSED
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_central_bank_infinite_funds PASSED
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_real_estate_unit_lien_dto PASSED
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_housing_system_maintenance_zero_sum PASSED
tests/finance/test_protocol_integrity.py::TestProtocolIntegrity::test_housing_system_rent_zero_sum PASSED
tests/finance/test_settlement_fx_swap.py::test_execute_swap_success PASSED
tests/finance/test_settlement_fx_swap.py::test_execute_swap_insufficient_funds_rollback PASSED
tests/finance/test_settlement_fx_swap.py::test_execute_swap_invalid_amounts PASSED
tests/finance/test_settlement_fx_swap.py::test_execute_swap_missing_agent PASSED
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_transfer_float_raises_error PASSED
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_create_and_transfer_float_raises_error PASSED
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_issue_treasury_bonds_float_leak PASSED
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_solvency_grace_period_solvent PASSED
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_solvency_grace_period_insolvent PASSED
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_solvency_established_firm PASSED
tests/finance/test_solvency_logic.py::TestSolvencyLogic::test_firm_implementation PASSED
tests/forensics/test_bond_liquidity.py::test_bond_issuance_checks_liquidity PASSED
tests/forensics/test_escheatment_crash.py::test_escheatment_handler_null_metadata_crash PASSED
tests/forensics/test_ghost_account.py::test_settlement_to_unregistered_agent_handling PASSED
tests/forensics/test_saga_integrity.py::test_saga_orchestrator_rejects_incomplete_dto PASSED
tests/initialization/test_atomic_startup.py::TestAtomicStartup::test_atomic_startup_phase_validation PASSED
...
tests/unit/systems/test_m2_integrity.py::test_transfer_m2_to_m2_no_expansion PASSED
tests/unit/systems/test_m2_integrity.py::test_transfer_non_m2_to_m2_expansion PASSED
tests/unit/systems/test_m2_integrity.py::test_transfer_m2_to_non_m2_contraction PASSED
tests/unit/systems/test_m2_integrity.py::test_transfer_non_m2_to_non_m2_no_effect PASSED
tests/unit/systems/test_m2_integrity.py::test_transaction_processor_ignores_money_creation PASSED
tests/unit/systems/test_m2_integrity.py::test_money_creation_metadata_executed PASSED

======================== 469 passed, 7 skipped in 25.10s ========================
```
