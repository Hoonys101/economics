# Spec: Solvency Check Engine

This document specifies the design for a stateless Solvency Check Engine for the Finance system.

## 1. Logic Steps (Pseudo-code)

```python
def engine_check(inputs: SolvencyCheckInputDTO) -> SolvencyCheckOutputDTO:
    # 1. Deconstruct input
    assets = inputs.total_assets
    liabilities = inputs.total_liabilities

    # 2. Basic validation
    if assets < 0 or liabilities < 0:
        raise InvalidInputError("Assets and liabilities cannot be negative.")

    # 3. Core Solvency Calculation
    net_worth = assets - liabilities
    is_solvent = net_worth > 0

    # 4. Calculate Financial Ratio
    # Handle division by zero if assets are zero.
    debt_to_asset_ratio = (liabilities / assets) if assets > 0 else 0.0

    # 5. Construct and return output DTO
    return SolvencyCheckOutputDTO(
        entity_id=inputs.entity_id,
        is_solvent=is_solvent,
        net_worth=net_worth,
        debt_to_asset_ratio=debt_to_asset_ratio,
    )
```

## 2. Exception Handling
- **`InvalidInputError`**: Raised if `total_assets` or `total_liabilities` are negative.

## 3. Interface Specification (DTO Summary)
- **Input**: `SolvencyCheckInputDTO` requires an `entity_id`, `total_assets`, and `total_liabilities`.
- **Output**: `SolvencyCheckOutputDTO` reports a boolean `is_solvent`, the calculated `net_worth`, and the `debt_to_asset_ratio`.

## 4. Verification & Testing Strategy
- **New Test Cases**:
  - `test_solvent_entity`: `assets > liabilities`, expect `is_solvent = True`.
  - `test_insolvent_entity`: `assets < liabilities`, expect `is_solvent = False`.
  - `test_borderline_solvency`: `assets == liabilities`, expect `is_solvent = False`.
  - `test_zero_assets_and_liabilities`: Expect `is_solvent = False`, `ratio = 0.0`.
  - `test_zero_assets_with_liabilities`: Expect `is_solvent = False`, `ratio = 0.0`.
  - `test_input_validation`: Test with negative asset/liability values.
- **Existing Test Impact**:
  - Minimal impact on existing tests as this is a new, isolated feature.
  - The new orchestrator (`FinanceSystem.check_solvency`) will need its own tests to verify it correctly sources asset/liability data and calls the engine.
- **Integration Check**: A new scenario should be created where a firm takes on excessive debt, fails the solvency check, and is correctly flagged for liquidation or bailout by the system.

## 5. Mocking Guide
- Tests for the `FinanceSystem` orchestrator method will inject a mock `SolvencyEngine`.
- Use the `golden_firms` and `golden_households` fixtures from `conftest.py` as a source for realistic asset/liability data to build `SolvencyCheckInputDTO` fixtures.

## 6. 🚨 Risk & Impact Audit
- **Data Aggregation Risk**: The primary risk lies in the orchestrator. Accurately calculating `total_assets` and `total_liabilities` for a complex entity (e.g., a firm with diverse inventory, financial instruments, and loans) is non-trivial. Bugs in the aggregation logic will lead to incorrect solvency assessments.
- **Definition of "Asset"**: The definition of an asset may be ambiguous. The orchestrator must have a clear policy on what is included (e.g., physical inventory, cash, accounts receivable) and how it is valued (e.g., market price, book value).
- **Performance**: For entities with a large number of assets/liabilities, the aggregation step could be a performance bottleneck. This should be considered during orchestrator implementation.

## 7. 🚨 Mandatory Reporting Verification
- An analysis of the complexities in defining and aggregating "total assets" and "total liabilities" across different agent types has been logged to `communications/insights/MS-0128-Solvency-Data-Aggregation.md`. This report is a prerequisite for implementation.
