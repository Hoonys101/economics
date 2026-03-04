# Memory Fix 4: Finance Ledger Compaction

## 1. Architectural Insights
Implemented `compact_ledger(self, current_tick: int) -> int` in `modules/finance/system.py` inside the `FinanceSystem` class.
The initially requested implementation snippet from the prompt contained `hasattr()` blocks and legacy field lookups.

To strictly adhere to **Protocol Purity**, **DTO Purity**, and **Zero-Sum Integrity** guardrails:
- Removed `hasattr()` checks.
- Iterated over typed structures (`ledger.banks.items()`, `ledger.treasury.bonds.items()`).
- Used structured DTO access for `loan.remaining_principal_pennies` as expected in `LoanStateDTO`.
- Modified `BondStateDTO` to add `is_settled: bool = False`.
- Refactored `modules/finance/engines/debt_servicing_engine.py` to correctly calculate and append the principal repayment transaction upon reaching maturity, and to flip the bond's `is_settled` flag to `True` only after this payout is processed.
- The condition to purge bonds from the ledger in `compact_ledger` now evaluates `bond.is_settled`, eliminating the critical "Debt Oblivion" defect where relying purely on `maturity_tick <= current_tick` could silently destroy government liabilities before principal settlement actually occurs.

## 2. Regression Analysis
- `pytest tests/finance/` and `pytest tests/simulation/` passed successfully with no new errors.
- Added bond principal transaction generation logic to the `debt_servicing_engine`.
- The fix prevents financial integrity violations without breaking existing components since the engine's interface and the DTO structural integrity are strictly preserved.

## 3. Test Evidence

```
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.STRICT, default_loop_scope=None
collected 49 items

tests/finance/test_bailout_logic.py ...                                  [  6%]
tests/finance/test_bank.py .......                                       [ 20%]
tests/finance/test_corporate_bonds.py .....                              [ 30%]
tests/finance/test_credit_system.py ...........                          [ 53%]
tests/finance/test_government.py ...                                     [ 59%]
tests/finance/test_loan_application.py ....                              [ 67%]
tests/finance/test_settlement_integrity.py ...                           [ 73%]
tests/finance/test_solvency_logic.py ....                                [ 81%]
tests/simulation/test_firm_factory.py ..                                 [ 85%]
tests/simulation/test_firm_refactor.py ...                               [ 91%]
tests/simulation/test_initializer.py .                                   [ 93%]

... (49 passed in 23.02s)
================================================================================
```
