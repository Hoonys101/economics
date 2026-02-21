File: simulation\orchestration\api.py
```python
from __future__ import annotations
from typing import Protocol, runtime_checkable, Any, Optional
from simulation.dtos.api import SimulationState, GovernmentSensoryDTO

@runtime_checkable
class IPhaseStrategy(Protocol):
    """
    Interface for a distinct execution phase within the TickOrchestrator.
    Each phase encapsulates a specific domain logic (e.g., Production, Transaction, Cleanup)
    and transforms the SimulationState.
    """
    def execute(self, state: SimulationState) -> SimulationState:
        """
        Executes the phase logic.
        
        Args:
            state: The current snapshot of the simulation state.
                   While the DTO itself is structurally immutable, it contains mutable
                   queues (transactions, effects) that phases populate.
        
        Returns:
            The potentially modified SimulationState. 
            (Note: In current implementation, it often returns the same instance, 
             but the contract allows for returning a new state DTO).
        """
        ...

@runtime_checkable
class IOrchestrator(Protocol):
    """
    Interface for the Central Simulation Orchestrator.
    Responsible for sequencing phases and managing the WorldState lifecycle.
    """
    def run_tick(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO] = None) -> None:
        """
        Executes a full simulation tick, running all registered phases in order.
        
        Args:
            injectable_sensory_dto: Optional DTO for injecting external/government 
                                    sensory data into the tick context.
        """
        ...

    def prepare_market_data(self) -> Any:
        """
        Prepares market data snapshots.
        Required for legacy integration with Simulation.py.
        """
        ...
```

File: design\3_work_artifacts\specs\lane3_dx_spec.md
```markdown
# Spec: Lane 3 Orchestrator & Test Recovery (DX Hardening)

## 1. Introduction
- **Goal**: Harden the `TickOrchestrator` against runtime fragility caused by missing DTO attributes and modernize the test suite to eliminate "Ghost Attributes" and legacy tax collection patterns.
- **Scope**:
  - `simulation/orchestration/tick_orchestrator.py` (Hardening)
  - `tests/unit/orchestration/test_phase_housing_saga.py` (Refactor to DTO)
  - `tests/unit/systems/test_tax_agency.py` (Modernization to `settle_atomic`)
  - `tests/unit/test_transaction_handlers.py` (Protocol Enforcement)
- **Key Deliverable**: A stable, crash-resistant Orchestrator and a passing test suite that respects `IFinancialAgent` and `HousingTransactionSagaStateDTO` contracts.

## 2. Technical Debt & Risk Audit
- **[TD-ARCH-ORCH-HARD] Orchestrator Fragility**: 
  - *Risk*: Current `_create_simulation_state_dto` accesses `state.government`, `state.bank` directly. In unit tests where `WorldState` is partially mocked, this raises `AttributeError`.
  - *Resolution*: Use defensive `getattr(state, 'attr', None)` with warning logging for critical components missing in non-zero ticks.
- **[TD-TEST-TAX-DEPR] Legacy Tax Tests**:
  - *Risk*: Tests use `Government.collect_tax` (which uses non-atomic `transfer`) while production uses `settle_atomic`. This creates false confidence.
  - *Resolution*: Rewrite tests to mock `settle_atomic` and verify `record_revenue`.
- **[TD-FIN-SAGA-ORPHAN] Saga Test Regression**:
  - *Risk*: Tests passing raw `dict` to `SagaOrchestrator` fail because `SagaOrchestrator` now expects strict `HousingTransactionSagaStateDTO` objects.
  - *Resolution*: Instantiate proper DTOs in test setup.

## 3. Detailed Design

### 3.1. TickOrchestrator Hardening (`simulation/orchestration/tick_orchestrator.py`)

**Logic (Pseudo-code for `_create_simulation_state_dto`)**:
```python
def _create_simulation_state_dto(self, injectable_sensory_dto: Optional[GovernmentSensoryDTO]) -> SimulationState:
    state = self.world_state
    
    # Defensive Retrieval with Warnings
    # Critical components that SHOULD exist after Tick 0
    government = getattr(state, "government", None)
    if not government and state.time > 0:
        logger.warning(f"ORCH_WARN | Government missing at tick {state.time}")
        
    bank = getattr(state, "bank", None)
    central_bank = getattr(state, "central_bank", None)
    
    # Optional components
    escrow_agent = getattr(state, "escrow_agent", None)
    stock_market = getattr(state, "stock_market", None)
    stock_tracker = getattr(state, "stock_tracker", None)
    
    # ... (Command Queue Draining Logic remains) ...

    return SimulationState(
        # ...
        primary_government=government,
        governments=[government] if government else [],
        bank=bank,
        central_bank=central_bank,
        escrow_agent=escrow_agent,
        stock_market=stock_market,
        stock_tracker=stock_tracker,
        # ...
        # Ensure 'transaction_processor' is checked
        transaction_processor=getattr(state, "transaction_processor", None),
        # ...
    )
```

### 3.2. Saga Test Refactor (`tests/unit/orchestration/test_phase_housing_saga.py`)

**Problem**: `test_phase_housing_saga_execution` passes a `dict` representing a saga.
**Fix**: Use `HousingTransactionSagaStateDTO`.

**Test Setup (Revised)**:
```python
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, HousingSagaStatus

def test_phase_housing_saga_execution(self, mock_world_state, phase):
    # Setup
    saga_dto = HousingTransactionSagaStateDTO(
        saga_id="saga-123",
        buyer_id=101,
        seller_id=202,
        property_id="prop-001",
        agreed_price=50000,
        status=HousingSagaStatus.INITIATED,
        created_tick=10,
        step_history=[],
        context={}
    )
    
    # Mock the orchestrator's active_sagas to return this DTO
    mock_world_state.saga_orchestrator.active_sagas = [saga_dto]
    
    # Execute
    phase.execute(mock_world_state)
    
    # Verify
    mock_world_state.saga_orchestrator.process_sagas.assert_called_once()
```

### 3.3. Tax Agency Test Modernization (`tests/unit/systems/test_tax_agency.py`)

**Problem**: Uses `collect_tax` and `mock_settlement.transfer`.
**Fix**:

```python
def test_collect_sales_tax_modern(self):
    # Setup
    tax_agency = self.tax_agency
    # Enforce Protocol on Settlement Mock
    tax_agency.settlement_system.settle_atomic.return_value = (True, "TX-TAX-001", None)
    
    # Execute (Directly call what the handler would call, or update the helper)
    # If testing TaxAgency helper:
    tax_agency.collect_sales_tax(payer_id=1, amount=100)
    
    # Verify
    tax_agency.settlement_system.settle_atomic.assert_called_once()
    # Ensure arguments structure:
    # (payer_id, gov_id, amount, currency, tax_type)
    call_args = tax_agency.settlement_system.settle_atomic.call_args
    assert call_args.kwargs['amount'] == 100
    assert call_args.kwargs['transaction_type'] == "TAX_SALES"
```

## 4. Verification Plan

### 4.1. Automated Tests
1.  **Orchestrator Stability**: 
    - Create `tests/unit/orchestration/test_tick_orchestrator_resilience.py`.
    - Test Case: `test_create_simulation_state_missing_components`: Initialize `TickOrchestrator` with a `WorldState` mock that lacks `government` and `bank`. Assert no `AttributeError` is raised and `SimulationState.primary_government` is `None`.
2.  **Saga Integration**:
    - Run `pytest tests/unit/orchestration/test_phase_housing_saga.py`.
    - Verify `process_sagas` receives strict DTOs.
3.  **Tax Modernization**:
    - Run `pytest tests/unit/systems/test_tax_agency.py`.
    - Verify all `transfer` calls are replaced by `settle_atomic`.

### 4.2. Manual Verification
- **Run Full Tick**: Execute `main.py --ticks 1` to ensure the hardened Orchestrator works with the real `WorldState` initialization flow.

## 5. Mandatory Reporting Instruction

**[ACTION REQUIRED]**
Upon completion of the implementation:
1. Generate a specialized insight report at `communications/insights/lane3-dx-spec.md`.
2. Document the specific "Ghost Attributes" found and removed from mocks.
3. List the test files that were refactored.
4. Include the final `pytest` output showing 100% pass rate.

**Example Content for Insight Report**:
```markdown
# Insight Report: Lane 3 DX Hardening
- **Mission**: lane3-dx-spec
- **Status**: Completed
- **Architectural Change**: 
  - `TickOrchestrator` now uses `getattr` for component access.
  - Tax tests aligned with `settle_atomic`.
- **Debt Resolved**: TD-ARCH-ORCH-HARD, TD-TEST-TAX-DEPR.
```

---
**[Scribe Note]**: This spec adheres to `SEO_PATTERN.md` (Stateless Engine) by ensuring the Orchestrator prepares the DTO state correctly for pure engines, and `TESTING_STABILITY.md` by enforcing strict Protocol mocking.
```