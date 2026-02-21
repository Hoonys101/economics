# Technical Audit Report: Lane 1 - Finance & M2 Logic

## Executive Summary
The financial engine is currently suffering from **M2 Negative Inversion (TD-ECON-M2-INV)**, where the aggregate money supply is reported as a negative value in diagnostic logs. This is caused by `WorldState.calculate_total_money()` failing to distinguish between liquid assets and liabilities (overdrafts), combined with a subtraction of bank reserves that leads to double-counting debt as a reduction in the money supply.

## Detailed Analysis

### 1. Trace of `MONEY_SUPPLY_CHECK` Failure
- **Status**: ❌ Integrity Failure
- **Trace**:
    - **Symptom**: `reports/diagnostic_refined.md` shows `MONEY_SUPPLY_CHECK` warnings starting at Tick 14, becoming massive negative values by Tick 20 (`Current: -47712322.00`).
    - **Logic Source**: `simulation/world_state.py:L161-203` (`calculate_total_money`).
    - **Root Cause**: 
        1. `calculate_base_money()` (L145) sums `holder.get_assets_by_currency()`. If an agent has a negative balance (overdraft), it directly reduces M0.
        2. `calculate_total_money()` then identifies banks and **subtracts** their reserves (L193). 
        3. If a bank is in overdraft (negative balance), subtracting a negative value increases M2, but if agents holding cash are actually just holding debt-backed digits that are already negative in the registry, the sum collapses.
        4. The removal of "Add Deposits" logic (L198) assumes agent wallets *are* deposits, but doesn't handle the case where those "deposits" are actually liabilities.
- **Evidence**: `TECH_DEBT_LEDGER.md` confirms this as `TD-ECON-M2-INV`.

### 2. Residual Float Precision Audit
- **Status**: ⚠️ Partial Implementation
- **Findings**:
    - **Settlement System**: `simulation/systems/settlement_system.py` has been successfully migrated to `int` pennies for `transfer` (L228) and `amount` validation (L229).
    - **World State**: `WorldState.get_total_system_money_for_diagnostics` (L205) still returns `float`, which explains why the diagnostic logs report values like `50431379.00` despite the underlying `int` representation.
    - **Tech Debt**: `TECH_DEBT_LEDGER.md` (TD-CRIT-FLOAT-CORE) notes that the `MatchingEngine` (not in current context) and `MAManager` still pass `float` prices to settlement.
- **Notes**: Floating point noise is present in the `MONEY_SUPPLY_CHECK` delta (e.g., `Delta: 130321.0000`), suggesting that while the storage is `int`, the reporting/comparison layer is still performing float arithmetic.

### 3. Hardened `IFinancialEntity` Proposal
To resolve the M2 inversion and prevent negative supply values, the `IFinancialEntity` protocol must enforce a distinction between assets and liabilities.

**Proposed Changes to `modules/finance/api.py`**:
```python
@runtime_checkable
class IFinancialEntity(Protocol):
    @property
    def liquid_balance_pennies(self) -> int:
        """Strictly non-negative cash on hand."""
        ...

    @property
    def liability_balance_pennies(self) -> int:
        """Outstanding short-term debt or overdrafts."""
        ...

    @property
    def balance_pennies(self) -> int:
        """Net balance: liquid_balance - liability_balance."""
        return self.liquid_balance_pennies - self.liability_balance_pennies

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds, prioritizing liability repayment."""
        ...
```

## Risk Assessment
- **Solvency Collapse**: Several firms (120, 121, 123) are closing down at Tick 20 with near-zero assets (`diagnostic_refined.md`). This coincides with the M2 inversion, suggesting that the simulation logic (interest rates/policy) is reacting to the negative money supply by crushing liquidity.
- **Race Conditions**: `TD-ARCH-STARTUP-RACE` shows that new firms (ID 124) are failing to launch because transactions are attempted before their accounts are registered in the `SettlementSystem`.

## Conclusion
The financial system is mathematically unstable due to the way overdrafts are aggregated into the M2 money supply. The "Money Supply" is being treated as a net position (Assets - Liabilities) at the aggregate level, rather than a measure of liquidity (Currency + Deposits). 

**Action Items**:
1. **Refactor `WorldState.calculate_total_money`**: Sum only positive liquid balances for M2; track liabilities as a separate "System Debt" metric.
2. **Harden `SettlementSystem`**: Implement the `open_account` blocking call to resolve `STARTUP_FAILED` errors for new firms.
3. **Quantize Reporting**: Update `get_total_system_money_for_diagnostics` to return `int` to eliminate float noise in logs.