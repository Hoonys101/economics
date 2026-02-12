# Mission Guide: SEO Hardening (Phase 15.2)

## 1. Objectives (TD-PH15-SEO-LEAKS)
- **Eliminate Layer Leaks**: Ensure that core engines and services receive only DTO Snapshots, never direct Agent object handles.
- **Enforce Statelessness**: Components should have no implicit reliance on the internal state of Agents accessed via object methods.

## 2. Target Components & Refactoring Plan

### A. `modules.government.tax.service.TaxService`
- **Current Issue**: `collect_wealth_tax` takes `List[IAgent]` and inspects attributes like `needs`, `is_employed`, and `get_balance`.
- **Refactor**:
    1. Define `WealthTaxTargetDTO` with fields: `agent_id`, `is_active`, `is_household`, `net_worth_pennies`.
    2. Update `collect_wealth_tax` signature to accept `List[WealthTaxTargetDTO]`.
    3. The Orchestrator (Government) is responsible for creating these DTOs from its registry.

### B. `modules.finance.system.FinanceSystem.evaluate_solvency`
- **Current Issue**: Takes `firm: 'Firm'` and accesses a deep hierarchy of internal states (`hr_state`, `finance_state`, `get_quantity`, etc.).
- **Refactor**:
    1. Define `FirmSolvencySnapshotDTO` with all necessary metrics for Altman Z-Score calculation (total assets, working capital, retained earnings, avg profit history).
    2. Update `evaluate_solvency` to accept this DTO.

### C. Sovereign Debt Context
- **Current Issue**: `issue_treasury_bonds` calculates `debt_to_gdp` by reaching into `self.government`.
- **Refactor**:
    1. Pass `current_gdp` and `total_sovereign_debt` as arguments or part of a `FiscalContextDTO`.

## 3. Reference Context (MUST READ)
- `modules/government/tax/service.py`
- `modules/finance/system.py`
- `design/1_governance/architecture/ARCH_PROTOCOLS.md` (if exists, or check QUICKSTART for SEO principles)

## 4. Verification
- `pytest tests/modules/government/test_tax_service.py`
- `pytest tests/modules/finance/test_finance_solvency.py`
- All tests must pass with ZERO direct agent attribute warnings.
