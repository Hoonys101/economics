# Mission Guide: Corporate & Finance Dept Upgrade [Bundle B]

This document outlines the multi-currency migration for Firms and the resolution of critical financial type errors.

## 1. Objectives
- **TD-213-B**: Complete multi-currency migration for Firms, metrics, and AI controllers.
- **TD-233**: Resolve Law of Demeter violation in `FinanceDepartment.process_profit_distribution`.
- **TD-240**: Fix `TypeError: unsupported operand type(s) for /: 'dict' and 'float'` in `calculate_altman_z_score`.

## 2. Reference Context (MUST READ)
- **Primary Spec**: [Multi-Currency Migration for Firms](file:///c:/coding/economics/design/3_work_artifacts/drafts/draft_232153__ObjectivenResolve_TD213B.md)
- **Critical Error Context**: The `calculate_altman_z_score` in `simulation/components/finance_department.py` is attempting to divide `working_capital` and `retained_earnings` by `total_assets`. After the migration, `total_assets` or its components may have become `Dict[CurrencyCode, float]` while the score logic expects `float`.

## 3. Implementation Roadmap

### Phase 1: Debug & Solvency Fix (TD-240)
1. In `FinanceDepartment.calculate_altman_z_score`, ensure all components (Balance, Capital Stock, Inventory) are converted to the **Primary Currency** before performing arithmetic operations.
2. Use the `_convert_to_primary` helper method.

### Phase 2: Multi-Currency Firm Logic (TD-213-B)
1. Update `FinanceDepartment` to track profit, cost, and revenue in `Dict[CurrencyCode, float]`.
2. Ensure `MarketSignalDTO` is currency-aware (using `MoneyDTO`).
3. Refactor AI decision inputs to use converted valuation/metrics.

### Phase 3: Encapsulation Hardening (TD-233)
1. Refactor profit distribution to use the established `portfolio` property or a DTO interface to query shareholder status, removing direct access to Agent private state.

## 4. Verification
- **Trace Leak**: `python scripts/trace_leak.py` MUST result in **0.0000 leak**.
- **Solvency Tests**: `pytest tests/unit/simulation/test_firms.py`
- Validate that Altman Z Score calculation returns a valid `float`.
