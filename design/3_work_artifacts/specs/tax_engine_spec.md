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
