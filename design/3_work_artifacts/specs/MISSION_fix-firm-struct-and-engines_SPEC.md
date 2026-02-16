# Mission Spec: Firm Structure & Engine Parity

## Goal
1. Decompose `Firm` agent using `InventoryComponent` and `FinancialComponent`.
2. Fix `TypeError` in `ai_driven_firm_engine.py`.
3. Fix unit mismatches in firm-related engines and tests.

## Context
The `Firm` agent still holds its own wallet and inventory dictionaries, violating the CES Lite component pattern. Additionally, recent migrations to integer pennies have caused mismatches in tests and engines.

## Identified Failures

### 1. Engine Logic (`ai_driven_firm_engine.py`)
- **[simulation/decisions/ai_driven_firm_engine.py:170](file:///c:/coding/economics/simulation/decisions/ai_driven_firm_engine.py#L170)**: 
  `TypeError: unsupported operand type(s) for *: 'Mock' and 'float'`.
  - **Fix**: Cast `best_bid` to float or check if it's a mock. In real simulation, ensure signals provide floats/ints.

### 2. Unit Mismatches
- **[tests/simulation/components/engines/test_asset_management_engine.py](file:///c:/coding/economics/tests/simulation/components/engines/test_asset_management_engine.py)**: `assert 0.5 == 0.01`.
  - **Fix**: Align test expected values with Penny standard (integers) or fix the unit calibration.
- **[tests/unit/components/test_engines.py](file:///c:/coding/economics/tests/unit/components/test_engines.py)**: `assert 10.0 == 1000`.
  - **Fix**: Expected 10 Dollars -> 1000 Pennies.

### 3. Firm Shell Refactor
- **[simulation/firms.py](file:///c:/coding/economics/simulation/firms.py)**:
  - Add `self.financial_comp = FinancialComponent(...)`
  - Add `self.inventory_comp = InventoryComponent(...)`
  - Delegate `IPortfolioHandler`, `IFinancialAgent`, and `IInventoryHandler` to these components.

## Verification
- Run `pytest tests/simulation/components/engines/test_asset_management_engine.py`
- Run `pytest tests/simulation/test_firm_refactor.py`
- Run `scripts/trace_leak.py`

### 📝 JULES Implementation Report
- **Status**: [/]
- **Self-Evaluation**: [Score 0-100]
- **Key Changes**: [List summary of refactored logic here]
