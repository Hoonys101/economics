# Tax Remediation Findings

**Date:** 2026-01-27
**Author:** Jules (Software Engineer)
**Related Tasks:** TD-110, TD-120

## Overview

As part of the remediation for **TD-110 (Phantom Tax Revenue)**, we enforced a strict `Settle -> Record` pattern in the `Government` class. The `Government.collect_tax` method has been marked as **DEPRECATED**.

During this process, an audit of the codebase revealed that the `TransactionProcessor` (`simulation/systems/transaction_processor.py`) heavily relies on this deprecated method.

## Findings: Legacy Usage in TransactionProcessor

The `TransactionProcessor` calls `Government.collect_tax` in the following contexts:

1.  **Escheatment (`escheatment`)**:
    -   Used to collect assets from deceased agents.
    -   Line ~100: `result = government.collect_tax(trade_value, "escheatment", buyer, current_time)`

2.  **Sales Tax (`goods`)**:
    -   Used to collect tax on goods transactions.
    -   Line ~142: `government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer, current_time)`

3.  **Labor Income Tax (`labor`, `research_labor`)**:
    -   **Firm Payer**: Line ~174: `government.collect_tax(tax_amount, "income_tax_firm", buyer, current_time)`
    -   **Household Payer**: Line ~184: `government.collect_tax(tax_amount, "income_tax_household", seller, current_time)`

4.  **Direct Tax Transaction (`tax`)**:
    -   Used for explicit tax transactions.
    -   Line ~211: `result = government.collect_tax(trade_value, tx.item_id, buyer, current_time)`

## Risks

*   **Phantom Revenue Risk (Mitigated):** The deprecated `Government.collect_tax` now correctly delegates to the atomic `TaxAgency.collect_tax` and `record_revenue`, so the immediate risk of recording revenue without settlement is mitigated.
*   **Maintenance Risk:** The `TransactionProcessor` is coupled to a deprecated method. Future changes to `Government` might break this if the deprecated method is removed.
*   **Performance/Architectural Risk:** The `TransactionProcessor` should ideally interact with the `TaxAgency` directly for collection logic, or use a specialized service, rather than treating `Government` as a pass-through.

## Recommendations (TD-120)

**TD-120: Refactor TransactionProcessor Tax Calls** has been created to address this. The refactoring should:

1.  Inject `TaxAgency` into `TransactionProcessor` (or access it via `Government` if necessary, but call `collect_tax` on the agency).
2.  Replace calls to `government.collect_tax` with:
    ```python
    result = government.tax_agency.collect_tax(...)
    if result['success']:
        government.record_revenue(result)
    ```
    Or a similar pattern that respects the atomic separation of settlement and recording.
