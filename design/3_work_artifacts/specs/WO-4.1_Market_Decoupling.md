# WO-4.1: Market Handler Abstraction (IBorrower Protocols)

**Status**: 🟢 Ready for Implementation (PR-Chunk #2)
**Target**: `modules/market/handlers/housing_transaction_handler.py`, `modules/housing/service.py`
**Goal**: Address `TD-215` by replacing `isinstance(..., Household)` with Protocol-based duck typing.

## 1. Scope of Work
- Define shared agent protocols in `modules/common/interfaces.py`.
- Refactor market logic to depend on these interfaces.

## 2. Implementation Details

### 2.1. Define Protocols (`modules/common/interfaces.py`)
Introduce `runtime_checkable` protocols:
- `IPropertyOwner`: fields `owned_properties`, methods `add_property`, `remove_property`.
- `IResident`: field `residing_property_id`, `is_homeless`.
- `IMortgageBorrower`: fields `id`, `assets: Dict`, `current_wage`.

### 2.2. Refactor Handlers
- **`housing_transaction_handler.py`**: Remove `from simulation.core_agents import Household`. Use `isinstance(buyer, IMortgageBorrower)` to trigger banking logic.
- **`housing/service.py`**: Use `isinstance(buyer, IPropertyOwner)` for registry updates.

## 3. Verification
- Verify that a mock class implementing `IMortgageBorrower` can successfully pass the handler test without being a `Household` instance.
