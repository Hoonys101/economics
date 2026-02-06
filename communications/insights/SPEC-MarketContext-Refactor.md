# Technical Insight Report: MarketContextDTO Refactoring

## 1. Problem Phenomenon
The codebase suffered from "parameter drilling" where `exchange_rates` (and potentially other market data) were passed individually through multiple layers of function calls (e.g., `Firm.generate_transactions` -> `HRDepartment.process_payroll`). This created several issues:
- **Fragility**: Adding a new piece of global market context (e.g., benchmark interest rates) required updating signatures across the entire call stack.
- **Inconsistency**: Different methods accepted different subsets of market data, leading to confusion about what data was available where.
- **SRP Violation**: `Firm.generate_transactions` contained logic for calculating marketing budgets, which should belong to the `SalesDepartment`.

## 2. Root Cause Analysis
- **Lack of Abstraction**: Global market context was not encapsulated in a dedicated Data Transfer Object (DTO).
- **Tight Coupling**: The `Firm` class acted as a "God Class", orchestrating too much logic that should have been delegated to its components (`HR`, `Finance`, `Sales`).
- **Legacy Patterns**: The system evolved from a single-currency model where passing a few floats was acceptable, to a multi-currency model where context became complex (`exchange_rates` dict).

## 3. Solution Implementation Details
To address these issues, we implemented the following changes:

### 3.1. `MarketContextDTO`
We defined a `TypedDict` named `MarketContextDTO` in `modules/system/api.py`.
```python
class MarketContextDTO(TypedDict):
    exchange_rates: Dict[CurrencyCode, float]
    benchmark_rates: Dict[str, float]
```
This DTO serves as the single source of truth for global market context during a simulation tick.

### 3.2. Standardization
We updated the following methods to accept `MarketContextDTO` instead of raw `exchange_rates`:
- `Firm.generate_transactions`
- `HRDepartment.process_payroll`
- `FinanceDepartment.generate_financial_transactions`
- `FinanceDepartment.calculate_valuation`
- `FinanceDepartment.finalize_tick`
- `SalesDepartment.adjust_marketing_budget`

### 3.3. Logic Delegation (SRP)
We moved the marketing budget calculation logic from `Firm.generate_transactions` to a new method `SalesDepartment.generate_marketing_transaction`. The `Firm` now delegates this responsibility:
```python
# In Firm.generate_transactions
tx_marketing = self.sales.generate_marketing_transaction(government, current_time, market_context)
```

### 3.4. Refactoring Support
- Updated `EconomicIndicatorTracker.capture_market_context` to return the new DTO structure.
- Updated `Phase_FirmProductionAndSalaries` and `Phase5_PostSequence` to construct/retrieve and pass the DTO.
- Created a `default_market_context` fixture for testing to ease the transition and ensure test coverage.

## 4. Lessons Learned & Technical Debt Identified
- **DTOs as Contracts**: Introducing DTOs early for cross-cutting concerns (like market context) prevents parameter drilling.
- **TypedDict vs Dataclass**: We opted for `TypedDict` for `MarketContextDTO` to allow for easy serialization and compatibility with existing dictionary-based flows, but `dataclasses` provide better type safety and immutability. The codebase currently mixes both (e.g., `DecisionInputDTO` is a dataclass holding a `MarketContextDTO` TypedDict). Future refactoring could unify these patterns.
- **Testing Overhead**: Refactoring core signatures requires widespread test updates. The use of shared fixtures (`tests/conftest.py`) significantly reduced the friction of this update.
- **Debt**: The `DecisionEngine` classes (`AIDrivenFirmDecisionEngine`, etc.) still rely heavily on `market_data` (legacy dict) and `market_snapshot`. While they have access to `market_context` via `DecisionContext`, they haven't fully migrated to using it for all global signals. This is a future optimization opportunity.
