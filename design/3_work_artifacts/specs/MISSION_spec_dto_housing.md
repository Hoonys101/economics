# MISSION_SPEC: WO-SPEC-DTO-HOUSING
## Goal
Decouple `HousingSystem`, `EstateRegistry`, and `HousingService` from `WorldState`.

## Context
Housing is a complex domain involving physical units and financial liens.

## Proposed Changes
1. Ensure `EstateRegistry` is a standalone service in the `GlobalRegistry`.
2. Refactor `HousingSystem` to accept `HousingMarketDTO`.
3. Decouple `RealEstateUnit` from global `transactions` list (use injected Ledger).

## Verification
- Run `pytest tests/unit/test_housing_system.py`.
