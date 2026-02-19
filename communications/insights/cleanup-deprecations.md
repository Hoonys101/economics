# Insight: Cleanup Deprecated Code (Track B)

## 1. Architectural Insights

### TD-DEPR-GOV-TAX: Atomic Tax Collection
Refactored `LaborTransactionHandler` to eliminate the use of `Government.collect_tax` (which wrapped `transfer` non-atomically).
- **Before**: `transfer(wage)` -> if success -> `collect_tax(tax)`
- **After**:
    - For Firm Payer: `settle_atomic(debits=[Firm], credits=[Household, Government])`. This is a true atomic transaction bundling wage and tax.
    - For Household Payer: `transfer(wage)` -> `settle_atomic(tax)`. This maintains the sequential nature required by fund availability but uses the new API.
- **Cleanup**: The `Government.collect_tax` method has been removed entirely. Attempts to use it will raise `AttributeError`.

### TD-DEPR-FACTORY: HouseholdFactory Standardization
Refactored `DemographicManager` to use `simulation.factories.household_factory.HouseholdFactory` correctly.
- **Fix**: The previous implementation was passing positional arguments blindly, resulting in type mismatches (`simulation` object passed as `new_id` int). Updated to use explicit keyword arguments (`parent=`, `new_id=`, `simulation=`).
- **Cleanup**: Deleted the deprecated `modules/household/factory.py` which was an inconsistent duplicate.
- **Integrity**: Initial asset transfer (birth gift) is now delegated to the Factory, ensuring encapsulation.

### TD-DEPR-STOCK-DTO: StockOrder Removal
Removed the legacy `StockOrder` class from `simulation/models.py`.
- **Standardization**: All market orders must now use `CanonicalOrderDTO`.
- **Adapter**: `tests/unit/test_market_adapter.py` was updated to remove legacy `StockOrder` input tests, while maintaining dictionary conversion tests for backward compatibility.

## 2. Test Evidence

### Government Tax Refactoring
`pytest tests/integration/test_government_tax.py tests/unit/agents/test_government.py`

```
tests/integration/test_government_tax.py::TestGovernmentTax::test_record_revenue_delegation PASSED [  8%]
tests/integration/test_government_tax.py::TestGovernmentTax::test_collect_tax_removed PASSED [ 16%]
tests/unit/agents/test_government.py::test_calculate_income_tax_delegation PASSED [ 25%]
tests/unit/agents/test_government.py::test_calculate_corporate_tax_delegation PASSED [ 33%]
tests/unit/agents/test_government.py::test_collect_tax_removed PASSED [ 41%]
tests/unit/agents/test_government.py::test_run_public_education_delegation PASSED [ 50%]
tests/unit/agents/test_government.py::test_deficit_spending_allowed_within_limit PASSED [ 58%]
tests/unit/agents/test_government.py::test_deficit_spending_blocked_if_bond_fails PASSED [ 66%]
```

### Market Adapter Refactoring
`pytest tests/unit/test_market_adapter.py`

```
tests/unit/test_market_adapter.py::TestMarketAdapter::test_pass_through PASSED [ 75%]
tests/unit/test_market_adapter.py::TestMarketAdapter::test_convert_dict_legacy_format PASSED [ 83%]
tests/unit/test_market_adapter.py::TestMarketAdapter::test_convert_dict_canonical_format PASSED [ 91%]
tests/unit/test_market_adapter.py::TestMarketAdapter::test_invalid_input PASSED [100%]
```

### Demographic Manager Refactoring
`pytest tests/unit/systems/test_demographic_manager_newborn.py`

```
tests/unit/systems/test_demographic_manager_newborn.py::test_newborn_receives_initial_needs_from_config PASSED [100%]
```
