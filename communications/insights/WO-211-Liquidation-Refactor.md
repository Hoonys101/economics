# Insight: WO-211 Refactoring LiquidationManager

## Overview
Refactored `LiquidationManager` to adhere to the Single Responsibility Principle (SRP) by extracting claim calculation logic into dedicated services (`HRService`, `TaxService`) and introducing an `AgentRegistry` for agent resolution.

## Changes
- Created `IHRService`, `ITaxService`, `IAgentRegistry` interfaces.
- Implemented `HRService`, `TaxService`, `AgentRegistry`.
- Refactored `LiquidationManager` to use these services instead of hardcoded logic.
- Updated `LifecycleManager` to initialize and inject these dependencies.
- Added and updated tests to verify the new architecture.

## Technical Debt & Observations
- **Mocking**: The `Firm` class was difficult to mock in unit tests due to `spec=Firm` enforcing class attributes while `finance` is added dynamically in `__init__`. Relaxed strict mocking for `firm` in `test_liquidation_manager.py`.
- **Imports**: Circular imports or `NameError` in `TYPE_CHECKING` blocks required careful handling of `from __future__ import annotations`.
- **Dependency Injection**: `LifecycleManager` is becoming a heavy composition root. Future refactoring might consider a dedicated DI container or factory.
- **Agent Registry**: `AgentRegistry` currently wraps `SimulationState.agents`. It needs to be explicitly updated with `set_state(state)` every tick in `LifecycleManager`. Added fallback logic to `get_agent` to ensure `government` is resolvable even if not present in the main `agents` dictionary during intermediate states.

## Verification
- Unit tests for `LiquidationManager` pass.
- Integration tests for `LiquidationServices` pass.
- Integration tests for `LiquidationWaterfall` pass.
