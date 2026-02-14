# Specification: Firm Agent Decomposition

## 1. Introduction
- **Objective**: Finalize the architectural refactoring of the `Firm` agent from a "Partial Orchestrator" to a "Pure Coordinator".
- **Scope**: Extract remaining business logic (Pricing, Liquidation) into stateless engines and enforce strict DTO-based communication patterns.
- **Context**: Current implementation (`simulation/firms.py`) contains residual logic that violates the Coordinator pattern.

## 2. Refactoring Strategy: Pricing Logic
- **Current**: `_calculate_invisible_hand_price` is a private method in `Firm`.
- **Target**: `PricingEngine.calculate_price(input: PricingInputDTO) -> PricingResultDTO`.
- **Agent Responsibility**:
    1. Construct `PricingInputDTO` from `SalesState` and `MarketSnapshot`.
    2. Call `PricingEngine`.
    3. Update `SalesState.last_prices` and log shadow metrics based on `PricingResultDTO`.

## 3. Refactoring Strategy: Liquidation Logic
- **Current**: `liquidate_assets` manually clears inventory/capital.
- **Target**: `AssetManagementEngine.calculate_liquidation(input: LiquidationExecutionDTO) -> LiquidationResultDTO`.
- **Agent Responsibility**: Apply the write-offs and return the `assets_returned` map.

## 4. Pseudocode
```python
def update_pricing(self, market_snapshot):
    input_dto = PricingInputDTO(
        item_id=item_id,
        current_price=self.sales_state.last_prices[item_id],
        market_snapshot=market_snapshot,
        config=self.config,
        unit_cost_estimate=self.production_state.unit_cost,
        inventory_level=self.inventory.get(item_id, 0),
        production_target=self.production_state.target
    )
    result = self.pricing_engine.calculate_price(input_dto)
    self.sales_state.last_prices[item_id] = result.new_price
```

## 5. Definition of Done
- `Firm` contains zero business logic methods.
- All engine interactions use `InputDTO` -> `Engine` -> `ResultDTO`.
- Existing test suite passes.
