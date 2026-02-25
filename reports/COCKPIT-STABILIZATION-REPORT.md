# 1. API Outline (`modules/system/command_pipeline/api.py`)

```python
from typing import Protocol, List, Any, runtime_checkable
from dataclasses import dataclass, field
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO

@dataclass(frozen=True)
class CommandBatchDTO:
    """
    Immutable DTO representing a drained batch of all system and god commands for a specific tick.
    Ensures unified command processing without fragmented queue access.
    """
    tick: int
    system_commands: List[SystemCommand] = field(default_factory=list)
    god_commands: List[GodCommandDTO] = field(default_factory=list)

@runtime_checkable
class ICommandIngressService(Protocol):
    """
    Unified Ingress Service for all external/Cockpit commands.
    Replaces fragmented queues in WorldState and direct WebSocket manipulation.
    """
    def enqueue_system_command(self, command: SystemCommand) -> None:
        """Enqueues a standard Cockpit/System command."""
        ...

    def enqueue_god_command(self, command: GodCommandDTO) -> None:
        """Enqueues a high-priority God-mode command."""
        ...

    def drain_for_tick(self, tick: int) -> CommandBatchDTO:
        """Atomically drains all internal queues into a single immutable DTO for the tick."""
        ...

@runtime_checkable
class IStateSanitizerService(Protocol):
    """
    Protocol to handle state mutations previously violating DTO purity in SimulationState.
    """
    def register_currency_holder(self, holder: Any) -> None:
        ...

    def unregister_currency_holder(self, holder: Any) -> None:
        ...
```

# 2. Specification Draft (`design/3_work_artifacts/specs/command_pipeline_spec.md`)

## 1. Overview
This specification addresses Cockpit Stabilization and Monetary Integrity by decoupling the `TickOrchestrator` God Class, establishing DTO purity for `SimulationState`, and unifying the command ingestion pipeline.

## 2. Mandatory Ledger Audit & Pre-Implementation Risk Analysis
### Technical Debt & Risk Assessment
- **TD-ARCH-ORCH-HARD (Orchestrator Fragility)**: Mocks lacking attributes break the simulation. Moving logic out of `TickOrchestrator` into decoupled Phase Strategies isolates this risk.
- **TD-TEST-MOCK-REGRESSION (Test Fragility)**: Altering `SimulationState` fields (removing `system_command_queue`, replacing with `CommandBatchDTO`) and removing `register_currency_holder` methods WILL break legacy mocks.
- **DTO/DAO Interface Impact**: Removing state-mutating methods from `SimulationState` requires updating `Household` and `Firm` initialization/teardown logic to use `IStateSanitizerService` instead.
- **Integration Check**: `test_transaction_engine.py` and `test_firm_brain_scan.py` must be audited to ensure zero-sum monetary flows still hold under the new command pipeline.

## 3. Logic Steps (Pseudo-Code)

### Step 3.1: Unify Command Ingress (`CommandIngressService`)
```python
class CommandIngressService(ICommandIngressService):
    def __init__(self):
        self._system_queue = deque()
        self._god_queue = deque()
        
    def enqueue_system_command(self, cmd: SystemCommand):
        self._system_queue.append(cmd)
        
    def drain_for_tick(self, tick: int) -> CommandBatchDTO:
        # Atomically extract and clear queues
        sys_cmds = list(self._system_queue)
        god_cmds = list(self._god_queue)
        self._system_queue.clear()
        self._god_queue.clear()
        return CommandBatchDTO(tick=tick, system_commands=sys_cmds, god_commands=god_cmds)
```

### Step 3.2: Refactor `server.py`
- Remove direct manipulation of `sim.command_service` or raw dictionaries.
- Pass validated `CockpitCommand` objects straight to `CommandIngressService`.

### Step 3.3: Cleanse `SimulationState` DTO (DTO Purity)
- **Remove** `register_currency_holder` and `unregister_currency_holder`.
- **Remove** fragmented `system_commands`, `god_command_snapshot`, `system_command_queue`.
- **Add** `command_batch: CommandBatchDTO`.

### Step 3.4: De-Bloat `TickOrchestrator`
- Move "Money Supply Verification (Tick 0)" and "Market Health Check (Breaker)" into a new `Phase0_PreTickMetrics(IPhaseStrategy)`.
- Move "Post-Tick M2 Leak Calculation" and "Market Panic Index Calculation" into a new `Phase6_PostTickMetrics(IPhaseStrategy)`.
- `TickOrchestrator` must ONLY coordinate phase execution and perform `_drain_and_sync_state`.

## 4. Testing & Verification Strategy
- **New Test Cases**: 
  - Verify `CommandIngressService` successfully atomizes multiple WS inputs into one `CommandBatchDTO`.
  - Verify M2 invariant constraints via `Phase6_PostTickMetrics`.
- **Existing Test Impact**: Update `tests/conftest.py` where `SimulationState` is mocked to ensure `command_batch` is provided and method calls to `register_currency_holder` are repointed.
- **Integration Check**: Complete an E2E simulation run for 60 ticks confirming `MONEY_SUPPLY_CHECK` Delta equals exactly 0.

## 5. Mandatory Reporting Instruction
**[REQUIRED ACTION FOR IMPLEMENTER]**: Upon completing this implementation or discovering further architectural anomalies during refactoring, you MUST log your findings inside the dedicated insight file at `communications/insights/COCKPIT_STABILIZATION.md`. Do NOT append notes to shared manuals.

# 3. Insight Report (`communications/insights/COCKPIT_STABILIZATION.md`)

```markdown
# Insight Report: COCKPIT_STABILIZATION

## 1. Architectural Insights
- **Command Queue Race Conditions**: `server.py` and `TickOrchestrator` previously accessed shared queue arrays directly from `WorldState` asynchronously. Creating `CommandIngressService` with atomic `drain_for_tick` removes asynchronous mutation risks during the simulation tick loop.
- **DTO Purity Violation Addressed**: `SimulationState` contained active business logic methods (`register_currency_holder`), creating implicit inter-phase dependencies and breaking the strict stateless engine pattern (SEO_PATTERN). By migrating this to `IStateSanitizerService` (which acts directly upon `WorldState`), `SimulationState` is restored to a pure data-transfer object.
- **Orchestrator De-Bloating**: The extraction of M2 tracking and circuit breakers out of `TickOrchestrator` into dedicated Pre/Post metrics phases ensures the orchestrator is no longer a business logic God Class, severely reducing regression risks for future system additions.

## 2. Regression Analysis & Testing Alignment
- **M2 Negative Inversion Context**: The massive leak (-9.6B by tick 60) was exacerbated by the orchestrator directly manipulating transient queues and skipping M2 syncs when bankruptcies occurred outside designated phases. By restricting all financial logic strictly to Settlement and M2 Post-Metrics phases, we can enforce zero-sum verification rigidly per-tick.
- **Mock Refactoring**: Legacy tests mocking `WorldState.system_commands` will inherently fail. All tests constructing `SimulationState` must be updated to inject `CommandBatchDTO` to conform to the new architecture. `MagicMock` instances must strictly implement `IPhaseStrategy` and `ICommandIngressService`.

## 3. Pending Technical Debt Updates
The following items should be added to `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` upon completion:
- **TD-ARCH-ORCH-HARD**: RESOLVED (Logic moved to dedicated Metric Phases)
- **TD-TEST-MOCK-REGRESSION**: RESOLVED (DTOs strictly typed, methods purged from `SimulationState`)
```