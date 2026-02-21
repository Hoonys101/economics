# Technical Audit Report: Finance & Accounting Deep-Dive

## Executive Summary
This audit confirms that while the migration to integer-based "pennies" is underway, critical float-pollution persists in core financial protocols (`IFinancialAgent`, `IDebtStatus`). The accounting logic currently lacks reciprocal expense tracking for material purchases, and the M2 calculation is vulnerable to inversion from negative cash balances (overdrafts).

---

## Detailed Analysis

### 1. TD-CRIT-FLOAT-CORE: Precision & Determinism Gap
- **Status**: ⚠️ Partial Implementation
- **Evidence**: 
    - `modules\finance\api.py:L361-364`: `IFinancialAgent.get_liquid_assets()` and `get_total_debt()` still return `float`.
    - `modules\finance\api.py:L214-225`: `LoanInfoDTO` and `DebtStatusDTO` use `float` for balances and principal.
    - `simulation\dtos\api.py:L38`: `TransactionData.price` and `quantity` remain `float`.
- **Root Cause**: Incomplete refactoring of legacy protocols. While DTOs like `MoneyDTO` have moved to `amount_pennies: int`, the interfaces used for decision-making and debt tracking still pass floats, risking rounding errors and non-deterministic simulation states.

### 2. TD-ECON-M2-INV: M2 Money Supply Inversion
- **Status**: ❌ Critical Integrity Risk
- **Evidence**: 
    - `simulation\systems\settlement_system.py:L386`: `total_m2 = (total_cash - bank_reserves) + total_deposits`.
    - `design\2_operations\ledgers\TECH_DEBT_LEDGER.md:L30`: "Negative money supply due to overdrafts subtracted from aggregate cash."
- **Root Cause**: The calculation treats negative balances (overdrafts) as negative cash rather than debt liabilities. In a bank run or systemic failure scenario, aggregate "cash" can mathematically drop below zero if system agents or insolvent banks are permitted to hold negative balances without a floor.

### 3. TD-SYS-ACCOUNTING-GAP: Asymmetric Expense Logging
- **Status**: ⚠️ Identified Logic Gap
- **Evidence**: 
    - `simulation\systems\accounting.py:L38-40`: The buyer expense block for `Firm` is explicitly `pass` for goods transactions.
    - `simulation\systems\accounting.py:L60-65`: Comments state that expense is delayed until usage (COGS).
- **Root Cause**: While theoretically sound for GAAP inventory accounting, the simulation requires real-time cash-flow tracking for GDP and sectoral profit analysis. The current "Inventory Debit" approach bypasses the P&L expense tracking, making firm profitability appear higher than reality until materials are consumed.

---

## Technical Proposals & Pseudo-Code

### 1. Integer Hardening (Solution for TD-CRIT-FLOAT-CORE)
Update `IFinancialAgent` and related DTOs to enforce `int` return types.
```python
# modules/finance/api.py
@runtime_checkable
class IFinancialAgent(Protocol):
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int: ... # Enforced
    def get_total_debt_pennies(self) -> int: ... # Replace get_total_debt() -> float
```

### 2. M2 Recalculation (Solution for TD-ECON-M2-INV)
Liquidity must be floored at zero for M2 supply calculations.
```python
# settlement_system.py refactor for M2
total_cash = sum(max(0, agent.balance_pennies) for agent in agents)
total_debt_claims = sum(abs(min(0, agent.balance_pennies)) for agent in agents)
# M2 = (Currency in Circulation) + (Deposits)
# Currency in Circulation = Floored Cash - Bank Reserves
```

### 3. Reciprocal Accounting (Solution for TD-SYS-ACCOUNTING-GAP)
Modify `AccountingSystem` to track immediate cash outflow as an expense category for better macro-tracking.
```python
# accounting.py modification
if isinstance(buyer, Firm):
    if tx_type == "goods":
        # Record as 'input_purchase_expense' to balance Seller 'sales_revenue'
        buyer.record_expense(amount, transaction.currency) 
```

---

## Conclusion
The financial system is currently in a "hybrid" state between legacy floats and the new penny-integer standard. To achieve zero-sum integrity, the project must:
1.  **Enforce Integer Returns**: Specifically in `IFinancialAgent` and `DebtStatusDTO`.
2.  **Recalculate M2**: Treat overdrafts as credit expansion (debt) rather than negative base money.
3.  **Close Accounting Gaps**: Implement reciprocal expense logging for all goods transfers to support accurate GDP reporting.

**Final Verdict**: **High Risk** due to M2 Inversion and Float pollution in core protocols. Immediate refactoring of `modules/finance/api.py` is required.