# Insight: Fetch Housing Unit Quality from Registry

## Context
During the generation of the housing market snapshot in `MarketSnapshotFactory`, the quality of housing units was previously hardcoded to `1.0`. This was because the `OrderDTO` used in the matching process lacked detailed quality information, which is critical for agents to make informed decisions about property value.

## Implementation Details
- **Registry Integration**: The `MarketSnapshotFactory._create_housing_snapshot` method was updated to reference `state.real_estate_units`.
- **Efficiency**: A local lookup map (`unit_map`) is constructed at the start of the snapshot generation to allow $O(1)$ lookup of unit details by ID, ensuring performance even with a large number of units.
- **Data Enrichment**: In addition to `quality` (mapped from the unit's `condition`), the `rent_price` is now also populated in the `HousingMarketUnitDTO`, providing a more complete picture of the asset.

## Technical Insights
1. **ID Parsing Dependency**: The implementation currently relies on the `item_id` format being `unit_{id}`. While consistent with the current `SimulationInitializer` and `Registry` logic, this is a coupling that could be improved by a centralized ID parsing utility or by including the unit ID directly in the `OrderDTO` metadata.
2. **Registry as SSoT**: This change reinforces the pattern that while orders handle the "flow" of commerce, the `Registry` (and the `real_estate_units` collection in `SimulationState`) remains the Single Source of Truth for "stock" attributes like quality and condition.
3. **Factory-Level Enrichment**: Factories are the ideal place to join transactional data (Orders) with stateful data (Registry) to create rich DTOs for agents, preventing the core simulation loop from becoming cluttered with DTO assembly logic.

## Technical Debt
- The ID parsing logic (`item_id.split("_")[1]`) is duplicated in spirit across several handlers. A unified `HousingIDUtility` would reduce the risk of regressions if the naming convention changes.
