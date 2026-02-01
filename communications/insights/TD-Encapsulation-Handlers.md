# Technical Debt: Encapsulation Violation in Transaction Handlers

## Issue Description
The `GoodsTransactionHandler` and `LaborTransactionHandler` were directly accessing and modifying internal state properties of the `Household` agent (`current_consumption`, `current_food_consumption`, and `labor_income_this_tick`).

This violated the Law of Demeter and encapsulation principles. Furthermore, `current_consumption` is a read-only property (delegating to a DTO), causing `AttributeError` when the handlers attempted to set it.

## Fix
Refactored the handlers to use the public API methods provided by the `Household` class:
- `Household.record_consumption(quantity, is_food)` replaced direct property assignment in `GoodsTransactionHandler`.
- `Household.add_labor_income(amount)` replaced direct property assignment in `LaborTransactionHandler`.

## Impact
- **Stability**: Prevents `AttributeError` at runtime.
- **Maintainability**: Decouples transaction handlers from the internal state structure of `Household`. If the underlying DTOs or state management logic change, the handlers remain unaffected as long as the public API contract is preserved.
- **Consistency**: Enforces the use of semantic methods for state mutations.
