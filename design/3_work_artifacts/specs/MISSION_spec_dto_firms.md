# MISSION_SPEC: WO-SPEC-DTO-FIRMS
## Goal
Decouple `FirmSystem`, `TechnologyManager`, and `MAManager` from `WorldState`.

## Context
Firm-related systems manage corporate lifecycles and R&D, often reaching into `WorldState` for market data.

## Proposed Changes
1. Pass `MarketStateDTO` (already defined in skeletons.py) to these systems.
2. Use `FirmStateDTO` for cross-firm interactions.
3. Segregate `SimulationState` into a subset DTO for R&D logic.

## Verification
- Run `pytest tests/unit/test_firm_system.py`.
