# Technical Debt Report: Bank Interface & System Architecture

## WO-080: Golden Fixture Migration (Migration Debt)

### Issue Description
The `Bank` class (`simulation/bank.py`) does not fully conform to the `IFinancialEntity` interface expected by the `FinanceSystem` (`modules/finance/system.py`). Specifically:
- `FinanceSystem` expects `withdraw(amount)` for transferring funds.
- `Bank` implemented `withdraw(depositor_id, amount)` for agent interactions.
- Python does not support method overloading, leading to a signature conflict.

### Current Workaround
A polymorphic `withdraw(*args)` method was implemented in `Bank` to handle both signatures dynamically. This is a fragile patch that relies on argument count checking.

### Recommended Resolution
1. **Interface Segregation**: Split `Bank` responsibilities into:
   - `IBankService`: For agents (`withdraw_deposit`, `deposit_cash`).
   - `IFinancialEntity`: For system transfers (`withdraw`, `deposit`).
2. **Refactor `Bank`**: Rename methods to be explicit (e.g., `agent_withdraw` vs `reserve_withdraw`) and update all call sites.
3. **Strict Interface**: Ensure `Bank` explicitly inherits from and implements `IFinancialEntity`.

---
This report was generated during WO-080 to document out-of-scope architectural issues encountered during test migration.
