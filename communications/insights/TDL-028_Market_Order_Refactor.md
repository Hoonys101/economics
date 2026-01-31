# Insight Report: Market Order Refactor (TDL-028)

## 1. Phenomenon
The legacy `Order` class was a mutable data structure used inconsistently across the codebase (sometimes as a raw dictionary, sometimes as a class). This led to:
- **Side-effect risks**: Decision engines could accidentally mutate orders after submission.
- **Type instability**: Inconsistent field names (`order_type` vs `side`, `price` vs `price_limit`).
- **Testing friction**: Difficulty in mocking and verifying order intent.

## 2. Cause
The initial implementation prioritized rapid prototyping, leading to "God Objects" and leaky abstractions where market logic and agent logic shared mutable state references.

## 3. Solution (Refactoring Strategy)
We implemented the **Phase 6/7 Standardized Order Protocol**:
1.  **Immutable Contract**: Introduced `OrderDTO` (frozen dataclass) in `modules/market/api.py`.
2.  **Field Standardization**: Renamed `order_type` -> `side` and `price` -> `price_limit` to align with financial industry standards (FIX protocol style).
3.  **Market Adaptation**: Refactored `OrderBookMarket` to accept immutable DTOs but convert them internally to a mutable `MarketOrder` representation for matching and partial fills.
4.  **Decision Engine Updates**: Updated `AIDrivenFirmDecisionEngine`, `FinanceManager`, `SalesManager`, `OperationsManager`, and `HRManager` to use `dataclasses.replace` for "modifying" orders (e.g., repricing logic), ensuring purity.

## 4. Technical Debt & Lessons Learned
- **FrozenInstanceError**: The transition to immutable DTOs exposed several locations where code assumed in-place mutation (e.g., `_apply_pricing_logic`). Using `dataclasses.replace` is the correct pattern.
- **Internal State vs. External Contract**: `OrderBookMarket` *must* maintain internal mutable state (`quantity` reduction during matching). Trying to force the *market internal logic* to be fully immutable is inefficient. The pattern of `External Immutable DTO -> Internal Mutable Entity` worked best.
- **Legacy Aliases**: Providing `@property` aliases in `OrderDTO` (`price` -> `price_limit`) helped during the transition but should be deprecated in Phase 8.
- **Integration Tests**: Verify end-to-end flows early. Unit tests passed because mocks accepted the new DTOs, but integration tests failed because the *instantiation* code in legacy components hadn't been updated.

## 5. Verification
- **Unit Tests**: Passed.
- **Integration Tests**: `tests/integration/test_decision_engine_integration.py` Passed.
- **System Integrity**: `scripts/trace_leak.py` confirmed 0.0000 leak, ensuring the refactor didn't break financial atomicity.
