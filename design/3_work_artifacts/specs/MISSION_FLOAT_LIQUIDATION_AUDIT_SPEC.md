# Technical Audit Report: Float-to-Int Migration (Stage 7)

## Executive Summary
The core financial engine (`SettlementSystem`) has successfully transitioned to `int` (pennies) for its internal operations. However, a significant "Float Leakage" exists in the DTO boundaries (`simulation/dtos/api.py`) and integration points, where monetary values are still cast to `float` for analytics and legacy compatibility. This report identifies these critical leakage points and outlines a modernization plan to enforce the Penny Standard across the entire system.

---

## Detailed Analysis

### 1. SettlementSystem Audit
- **Status**: ✅ Implemented (Internal) / ⚠️ Partial (Integration)
- **Evidence**: `settlement_system.py:L140, L184, L247`
- **Findings**: 
    - Internal methods (`transfer`, `settle_atomic`, `get_balance`) strictly use `int` for amounts.
    - `record_liquidation` correctly processes `inventory_value` and `capital_value` as `int`.
    - **Leakage Point**: `_create_transaction_record` (L318) passes `price=1` and `quantity=amount`. If the `Transaction` model (simulation/models.py) still defines these as `float`, precision loss occurs during persistence.
    - **Technical Debt**: `TD-TRANS-LEGACY-PRICING` confirms that `TransactionProcessor` (integration layer) still performs `float` casting for `SettlementResultDTO`.

### 2. DTO Boundary Audit (The "Red Zone")
- **Status**: ❌ Missing (Critical Leakage)
- **Evidence**: `simulation/dtos/api.py:L28, L41, L59, L80`
- **Findings**: The DTOs responsible for state transfer and analytics are almost entirely `float`-based:
    - `TransactionData`: `quantity: float`, `price: float` (L28-29).
    - `AgentStateData`: `assets: Dict[CurrencyCode, float]` (L41).
    - `EconomicIndicatorData`: `avg_wage`, `food_avg_price`, `total_household_assets` are all `float` (L59-70).
    - `StockMarketHistoryData`: `stock_price`, `dividend_paid`, `market_cap` are `float` (L223-233).
    - `HouseholdIncomeData`: `labor_income`, `total_income` are `float` (L264-268).

### 3. MatchingEngine & Price Discovery
- **Status**: ⚠️ Partial
- **Evidence**: `TECH_DEBT_LEDGER.md:TD-MKT-FLOAT-MATCH`
- **Findings**: While the ledger claims `TD-MKT-FLOAT-MATCH` is "Resolved," the description still warns of "Financial Dust" from mid-price calculations. If `MatchingEngine` produces `float` prices that are then passed to `SettlementSystem`, the `int` cast in `SettlementSystem.transfer` will truncate values, violating Zero-Sum integrity.

---

## Migration Spec (Instructions for Jules)

1.  **Refactor DTOs (`simulation/dtos/api.py`)**:
    - Convert `price`, `assets`, `wage`, `income`, `profit`, and `dividend` fields from `float` to `int`.
    - Rename fields to `xxx_pennies` where disambiguation is needed (e.g., `assets` -> `assets_pennies`).
2.  **Abolish Bridges**:
    - Remove the `float` casting logic in `TransactionProcessor` (Ref: `TD-TRANS-LEGACY-PRICING`).
    - Update `SettlementResultDTO` to return `int` values only.
3.  **MatchingEngine Integer Math**:
    - Force mid-price calculations to use floor division: `(bid + ask) // 2`.
    - Ensure all order matching logic outputs integer prices to the `SettlementSystem`.

---

## Test Modernization Spec

### 1. Affected Test Files
- `tests/test_settlement_system.py`
- `tests/test_fiscal_integrity.py`
- `tests/test_matching_engine.py`
- `tests/integration/test_economy_flow.py`

### 2. Assertion Modernization
- **Replace**: `assert agent.assets == 100.50`
- **With**: `assert settlement_system.get_balance(agent.id) == 10050`
- **Constraint**: Prohibit the use of `pytest.approx` for monetary assertions. Any difference $> 0$ pennies is a Zero-Sum violation.

### 3. Fixture Update
- Update `conftest.py` and local `setup` methods to initialize balances as integers.
- Example: `agent.deposit(10000)` instead of `agent.assets = 100.0`.

---

## Risk Assessment
- **Truncation Error**: Staggered migration (where some systems send floats and others expect ints) will lead to $1$ penny discrepancies per transaction due to `int()` truncation.
- **Reporting Desync**: Dashboards/UI relying on `simulation/dtos/api.py` will display values $100x$ larger until the frontend is updated to divide by $100$.

## Conclusion
The backend "engine" is ready, but the "dashboard" and "transmission" (DTOs) are still leaking floats. The next phase must focus on an **Atomic DTO Refactor** to prevent "Financial Dust" from corrupting the simulation state.