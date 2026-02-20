# Phase 23 Mission 1: Operation Safety Net (Test Infrastructure)

## 1. Introduction

- **Mission Key**: `phase23-spec-safety-net`
- **Purpose**: To restore trust in the test suite by aligning mocks with architectural protocols (`ITransactionParticipant`) and updating lifecycle/cockpit assumptions to match the current `TickOrchestrator` implementation.
- **Scope**: 
  - `tests/utils/mocks.py` (New/Refactor): Create strict protocol-compliant mocks.
  - `tests/system/test_engine.py`: Update lifecycle tests to respect `_drain_and_sync_state`.
  - `tests/system/test_cockpit.py` (if exists) or relevant sections in `test_engine.py`: Fix deprecated command queue usage.

## 2. Architectural Risks & Constraints (Addressed)

- **Mock-Protocol Divergence (TD-TEST-TX-MOCK-LAG)**:
  - **Risk**: `MagicMock` fails `isinstance(mock, Protocol)` checks, causing false negatives in protocol enforcement logic.
  - **Solution**: Implement `MockAgent` class that explicitly inherits from `ITransactionParticipant` and `ICurrencyHolder`.
- **Lifecycle Orchestration Bypass (TD-TEST-LIFE-STALE)**:
  - **Risk**: Tests manually calling `death_system.execute()` miss critical queue draining logic handled by `TickOrchestrator`.
  - **Solution**: Tests must either use the Orchestrator or explicitly replicate `_drain_and_sync_state`.
- **SimulationState "God Object" Fragility**:
  - **Risk**: Manual construction of `SimulationState` in tests leads to "State Drift" and brittle tests.
  - **Solution**: Introduce `SimulationStateBuilder` in test utils.

## 3. Detailed Design

### 3.1. Component: Strict Mock Infrastructure (`tests/utils/mocks.py`)

**Objective**: Provide a reliable mock agent that passes protocol checks.

```python
from typing import Dict, Any, Optional
from modules.system.api import AgentID, CurrencyCode, DEFAULT_CURRENCY
from modules.simulation.api import ITransactionParticipant, ICurrencyHolder

class MockAgent(ITransactionParticipant, ICurrencyHolder):
    """
    A strict mock agent for testing that satisfies Protocol checks.
    Replaces loose MagicMock usage in test_engine.py.
    """
    def __init__(self, agent_id: AgentID, initial_balance: int = 0):
        self.id = agent_id
        self.wallet: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: initial_balance}
        self.inventory: Dict[str, float] = {}
        # Explicit Protocol Flag for runtime checks if needed
        self._is_transaction_participant = True 

    # ICurrencyHolder Implementation
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.wallet.get(currency, 0)

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        return self.wallet.copy()
    
    # ITransactionParticipant Implementation (Partial/Mock)
    def receive_payment(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet[currency] = self.wallet.get(currency, 0) + amount

    def deduct_payment(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> bool:
        current = self.wallet.get(currency, 0)
        if current >= amount:
            self.wallet[currency] = current - amount
            return True
        return False
        
    def add_item(self, item_id: str, quantity: float) -> None:
        self.inventory[item_id] = self.inventory.get(item_id, 0.0) + quantity

    def remove_item(self, item_id: str, quantity: float) -> bool:
        current = self.inventory.get(item_id, 0.0)
        if current >= quantity:
            self.inventory[item_id] = current - quantity
            return True
        return False

    # Mock specific helper
    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY):
        self.wallet[currency] = self.wallet.get(currency, 0) + amount
```

### 3.2. Component: Simulation State Builder (`tests/utils/builders.py`)

**Objective**: Centralize `SimulationState` creation to prevent "God Object" drift in tests.

```python
from dataclasses import dataclass, field
from unittest.mock import MagicMock
from simulation.dtos.api import SimulationState
# ... imports ...

class SimulationStateBuilder:
    def __init__(self):
        self.state_data = {
            "time": 0,
            "households": [],
            "firms": [],
            "agents": {},
            "markets": {},
            "primary_government": MagicMock(),
            "governments": [],
            "bank": MagicMock(),
            "central_bank": MagicMock(),
            "goods_data": {},
            "market_data": {},
            "config_module": MagicMock(),
            "tracker": MagicMock(),
            "logger": MagicMock(),
            "ai_training_manager": None,
            "ai_trainer": None,
            "transaction_processor": MagicMock(), # Default Mock
            "system_commands": [],
            "god_command_snapshot": [],
            "inter_tick_queue": [],
            "effects_queue": [],
            "inactive_agents": {},
            "currency_holders": [],
            # ... all other fields with safe defaults
        }

    def with_agents(self, households, firms):
        self.state_data["households"] = households
        self.state_data["firms"] = firms
        self.state_data["agents"] = {a.id: a for a in households + firms}
        return self

    def with_commands(self, system_commands):
        self.state_data["system_commands"] = system_commands
        return self

    def build(self) -> SimulationState:
        return SimulationState(**self.state_data)
```

### 3.3. Lifecycle Test Updates (`tests/system/test_engine.py`)

**Objective**: Fix `test_handle_agent_lifecycle_removes_inactive_agents`.

**Refactoring Strategy**:
1.  **Use Builder**: Replace manual `SimulationState` init with `SimulationStateBuilder`.
2.  **Mock Orchestrator Logic**: Instead of calling `death_system.execute(state)` directly and asserting state changes that *should have happened* via `_drain_and_sync_state`, we must:
    *   Call `death_system.execute(state)`.
    *   **Manually invoke** the sync logic (or a helper function that mimics it) to ensure `inactive_agents` in `SimulationState` are propagated to the `WorldState` mock (or the test variables).
    *   *Alternative*: Use a simplified `TickOrchestrator` for the test if feasible, but that might be too heavy.
    *   *Chosen Approach*: Explicitly verify the side-effects in `SimulationState` first, then verify the "sync" logic separately if needed, OR mock the `TickOrchestrator._drain_and_sync_state` method.

**Pseudo-code Update**:
```python
def test_handle_agent_lifecycle_removes_inactive_agents(self, setup_simulation_for_lifecycle):
    # ... setup ...
    
    # 1. Build State using Builder
    state_dto = SimulationStateBuilder()\
        .with_agents(sim.households, sim.firms)\
        .build()

    # 2. Mark Agents Inactive
    household_inactive.is_active = False
    
    # 3. Execute Phase Logic
    sim.lifecycle_manager.death_system.execute(state_dto)
    
    # 4. Verify DTO State (The Phase's immediate output)
    assert household_inactive.id in state_dto.inactive_agents
    
    # 5. Verify Synchronization (Simulating Orchestrator's role)
    # This confirms that if the Orchestrator does its job, the WorldState updates correctly.
    sim.inactive_agents.update(state_dto.inactive_agents)
    
    # 6. Final Assertions
    assert household_inactive.id in sim.inactive_agents
```

### 3.4. Cockpit Mock Alignment (`tests/system/test_cockpit.py` or similar)

**Objective**: Remove `system_command_queue`.

**Refactoring Strategy**:
- Identify tests injecting into `sim.system_command_queue`.
- Change to injecting into `sim.system_commands` (List) or using `CockpitOrchestrator.inject_command()`.
- Ensure `SimulationStateBuilder` populates `system_commands` from the list, not the deprecated queue.

## 4. Verification Plan

### 4.1. Automated Verification
- Run: `pytest tests/system/test_engine.py -v`
- Run: `pytest tests/utils/test_mocks.py` (New test to verify `MockAgent` complies with Protocol)

### 4.2. Protocol Compliance Check
- Add a temporary test case:
  ```python
  def test_mock_protocol_compliance():
      mock_agent = MockAgent(1)
      assert isinstance(mock_agent, ITransactionParticipant)
      assert isinstance(mock_agent, ICurrencyHolder)
  ```

## 5. Mandatory Reporting Instruction

**CRITICAL**: Upon completion of the code implementation, you must create a new file `communications/insights/phase23-spec-safety-net.md` containing:
1.  **Diff Summary**: What files were touched.
2.  **Test Evidence**: The output of the passed tests (especially the protocol compliance check).
3.  **Debt Resolution**: Confirmation that `TD-TEST-TX-MOCK-LAG` and `TD-TEST-LIFE-STALE` are resolved.

**Do not append to any existing report files.**