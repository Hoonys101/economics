# MISSION_SPEC: WO-SPEC-DTO-ANALYTICS
## Goal
Decouple `EconomicIndicatorTracker`, `InequalityTracker`, `StockMarketTracker`, and `AnalyticsSystem` from direct `WorldState` dependency.

## Context
These trackers currently pull data from `WorldState` attributes. They should instead receive specific "Observation DTOs" during the update phase.

## Proposed Changes
1. Define `AnalyticsObservationDTO` containing required metrics.
2. Refactor `Simulation.update()` to assemble this DTO.
3. Pass DTO to trackers instead of the whole `WorldState`.

## Verification
- Run `pytest tests/unit/test_analytics.py` (if available) or verify telemetry output.
