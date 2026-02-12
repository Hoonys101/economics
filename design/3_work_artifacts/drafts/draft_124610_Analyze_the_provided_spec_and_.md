# [DRAFT] PR-0128: SEO Hardening for TaxService and FinanceSystem Solvency Check

This draft outlines the new DTOs, API interfaces, and specifications for the requested refactoring and feature implementation.

---
## File: `modules/finance/tax/api.py` (New File)
```python
"""
Public API for the stateless Tax Calculation Engine.

This API defines the data structures (DTOs) and the interface (protocol)
for calculating taxes in a stateless, purely functional manner. The engine
takes all necessary data in an input DTO and returns all results in an
output DTO, without causing any side effects.
"""

from typing import TypedDict, Protocol, List

# ==============================================================================
# Data Transfer Objects (DTOs)
# ==============================================================================

class TaxBracketDTO(TypedDict):
    """Defines a single tax bracket with a rate and income threshold."""
    rate: float
    threshold: float

class TaxPayerDetailsDTO(TypedDict):
    """
    Input DTO containing all necessary information for tax calculation.
    This object provides the data context for a single tax calculation event.
    """
    entity_id: str
    taxable_income: float
    property_value: float

class TaxSystemConfigDTO(TypedDict):
    """
    Configuration DTO containing tax rates and brackets.
    This represents the state of the tax law for a given calculation.
    """
    income_tax_brackets: List[TaxBracketDTO]
    corporate_tax_rate: float # Applies if entity is a firm
    property_tax_rate: float

class TaxCalculationInputDTO(TypedDict):
    """The complete input for the tax engine."""
    payer_details: TaxPayerDetailsDTO
    system_config: TaxSystemConfigDTO

class TaxCalculationOutputDTO(TypedDict):
    """
    Output DTO containing the results of a tax calculation.
    """
    entity_id: str
    income_tax_due: float
    property_tax_due: float
    corporate_tax_due: float
    total_tax_due: float
    effective_income_tax_rate: float

# ==============================================================================
# Engine Interface
# ==============================================================================

class TaxEngine(Protocol):
    """
    A stateless engine for calculating taxes.

    This protocol defines the contract for a pure function that calculates
    taxes based on provided input data, without external dependencies or
    side effects.
    """

    def calculate(self, inputs: TaxCalculationInputDTO) -> TaxCalculationOutputDTO:
        """

        Calculates all applicable taxes for a given entity.

        Args:
            inputs: A DTO containing the payer's financial details and the
                    current tax system configuration.

        Returns:
            A DTO containing a detailed breakdown of all calculated taxes.
        """
        ...

```

---
## File: `design/3_work_artifacts/specs/tax_engine_spec.md` (New File)
````markdown
# Spec: Tax Calculation Engine (SEO Hardening)

This document specifies the design for a stateless Tax Calculation Engine, as part of the SEO (Stateless Engine, Orchestrator) hardening initiative.

## 1. Logic Steps (Pseudo-code)

```python
def engine_calculate(inputs: TaxCalculationInputDTO) -> TaxCalculationOutputDTO:
    # 1. Deconstruct input DTOs for clarity
    payer = inputs.payer_details
    config = inputs.system_config
    
    # 2. Initialize results
    income_tax = 0.0
    last_bracket_threshold = 0.0
    
    # 3. Calculate Progressive Income Tax
    # Ensure brackets are sorted by threshold
    sorted_brackets = sorted(config.income_tax_brackets, key=lambda b: b['threshold'])
    
    for bracket in sorted_brackets:
        if payer.taxable_income > bracket.threshold:
            taxable_in_bracket = bracket.threshold - last_bracket_threshold
            income_tax += taxable_in_bracket * bracket.rate
            last_bracket_threshold = bracket.threshold
        else:
            taxable_in_bracket = payer.taxable_income - last_bracket_threshold
            income_tax += taxable_in_bracket * bracket.rate
            break # No more income to tax
            
    # If income exceeds highest bracket, tax the remainder at the highest rate
    if payer.taxable_income > last_bracket_threshold:
        remainder = payer.taxable_income - last_bracket_threshold
        income_tax += remainder * sorted_brackets[-1].rate

    # 4. Calculate Property Tax
    property_tax = payer.property_value * config.property_tax_rate
    
    # 5. Calculate Corporate Tax (TBD: logic for identifying a corporation)
    # This is a placeholder; orchestrator should determine if entity is a firm.
    corporate_tax = 0.0 
    # if is_firm(payer.entity_id):
    #    corporate_tax = payer.taxable_income * config.corporate_tax_rate
        
    # 6. Aggregate results
    total_tax = income_tax + property_tax + corporate_tax
    effective_rate = (income_tax / payer.taxable_income) if payer.taxable_income > 0 else 0.0
    
    # 7. Construct and return output DTO
    return TaxCalculationOutputDTO(
        entity_id=payer.entity_id,
        income_tax_due=income_tax,
        property_tax_due=property_tax,
        corporate_tax_due=corporate_tax,
        total_tax_due=total_tax,
        effective_income_tax_rate=effective_rate,
    )

```

## 2. Exception Handling
- **`InvalidInputError`**: Raised if `taxable_income` or `property_value` are negative.
- **`ConfigurationError`**: Raised if `income_tax_brackets` is empty or not sorted correctly.

## 3. Interface Specification (DTO Summary)
- **Input**: `TaxCalculationInputDTO` bundles `TaxPayerDetailsDTO` (ID, income, property value) and `TaxSystemConfigDTO` (rates, brackets).
- **Output**: `TaxCalculationOutputDTO` provides a full breakdown of taxes due and the effective rate.

## 4. Verification & Testing Strategy
- **New Test Cases**:
  - `test_income_in_lowest_bracket`: Payer income falls entirely within the first tax bracket.
  - `test_income_spanning_multiple_brackets`: Payer income spans three brackets.
  - `test_income_exceeding_highest_bracket`: Payer income is higher than the top bracket's threshold.
  - `test_zero_income`: Payer has zero income and zero property, expecting zero tax.
  - `test_property_tax_only`: Payer has property value but zero income.
  - `test_input_validation`: Test for negative income values.
- **Existing Test Impact**:
  - All existing tests for `TaxService` will be broken.
  - The `TaxService` will become an orchestrator. Its tests must be rewritten to:
    1. Mock the new `TaxEngine`.
    2. Verify the orchestrator correctly queries for agent state (income, assets).
    3. Verify it correctly constructs the `TaxCalculationInputDTO`.
    4. Verify it correctly processes the `TaxCalculationOutputDTO` (e.g., by debiting the agent's account).
- **Integration Check**: The `run_taxes` step in the main simulation loop must pass, with government receiving the correct total tax revenue.

## 5. Mocking Guide
- Tests for the orchestrator (`TaxService`) will inject a mock `TaxEngine`.
- The mock engine should return a pre-defined `TaxCalculationOutputDTO`.
- Do NOT mock individual DTOs. Use `TypedDict` to create real data fixtures.
- **🚨 Schema Change Notice**: DTO changes require updating golden data for `Government` and `Household` agents if their financial records are used in integration tests. This will require running `scripts/fixture_harvester.py`.

## 6. 🚨 Risk & Impact Audit
- **Refactoring Cascade**: This is a high-impact change. `TaxService` is a core module. All direct callers will break and need to be updated to use the new orchestrator pattern.
- **Data Provenance**: The orchestrator is now responsible for gathering `taxable_income` and `property_value`. This could introduce bugs if the data sources are incorrect or inconsistent.
- **Circular Dependency Risk**: Low. The engine is stateless and only depends on DTOs, preventing it from importing other system modules.
- **Precedent Work**: A full audit of `TaxService` call sites must be performed (`scripts/analyze_call_sites.py`) to map out the full scope of the refactoring effort.

## 7. 🚨 Mandatory Reporting Verification
- Insights regarding the ambiguity of `taxable_income` (e.g., gross vs. net, capital gains) and the old `TaxService`'s stateful dependencies have been logged to `communications/insights/MS-0128-Tax-Engine-Refactor.md`. This report is a prerequisite for implementation.
````

---
## File: `modules/finance/api.py` (Additions)
```python
"""
Public API for the Finance System.
"""
# ... (existing content of api.py) ...

# ==============================================================================
# === ADDITIONS FOR SOLVENCY CHECK ENGINE
# ==============================================================================

from typing import TypedDict, Protocol

# --- Data Transfer Objects (DTOs) ---

class SolvencyCheckInputDTO(TypedDict):
    """Input DTO containing an entity's asset and liability totals."""
    entity_id: str
    total_assets: float
    total_liabilities: float

class SolvencyCheckOutputDTO(TypedDict):
    """Output DTO reporting the results of a solvency check."""
    entity_id: str
    is_solvent: bool
    net_worth: float
    debt_to_asset_ratio: float # liabilities / assets


# --- Engine Interface ---

class SolvencyEngine(Protocol):
    """
    A stateless engine for checking the financial solvency of an entity.
    """

    def check(self, inputs: SolvencyCheckInputDTO) -> SolvencyCheckOutputDTO:
        """
        Evaluates solvency based on assets and liabilities.

        Args:
            inputs: A DTO containing the entity's total assets and liabilities.

        Returns:
            A DTO reporting solvency status, net worth, and key ratios.
        """
        ...
```

---
## File: `design/3_work_artifacts/specs/finance_solvency_spec.md` (New File)
````markdown
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
````