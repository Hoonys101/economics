# Lifecycle Manager Initialization & Cycle Fix (`spec-lifecycle-init-fix.md`)

## 1. Introduction
- **Purpose**: Resolve the critical `ValueError: IHouseholdFactory is mandatory` failure preventing test execution and system stability.
- **Scope**: `AgentLifecycleManager` (init logic) and associated Integration/Unit tests.
- **Goals**:
    1.  Enforce `IHouseholdFactory` as a strict dependency in `AgentLifecycleManager` (remove `Optional`).
    2.  Fix `test_wo167_grace_protocol.py` and `test_lifecycle_reset.py` by injecting proper mocks.
    3.  Verify no circular import cycles exist between `Lifecycle`, `Birth`, and `Factory`.

## 2. Technical Context
- **Root Cause**: `AgentLifecycleManager` requires `IHouseholdFactory` for its `BirthSystem` submodule but defines it as `Optional` in `__init__`, leading to runtime errors when tests (or legacy code) rely on the default `None`.
- **Architectural Impact**:
    - **TD-ARCH-LIFE-GOD**: The Lifecycle Manager is a monolith composing `Birth`, `Death`, `Aging`. `BirthSystem` *requires* a Factory. Therefore, the Manager *must* require it.
    - **DI Pattern**: Moving from "Default None" to "Constructor Injection" aligns with the project's DI standards.

## 3. Detailed Design

### 3.1. Component: `AgentLifecycleManager` (`simulation/systems/lifecycle_manager.py`)

- **Change**: Update `__init__` signature.
- **Logic**:
    - Remove `Optional[IHouseholdFactory] = None`.
    - Make `household_factory` a positional or mandatory keyword argument.
    - Remove `if household_factory is None: raise ValueError(...)`.

```python
# pseudo-code update
class AgentLifecycleManager(AgentLifecycleManagerInterface):
    def __init__(self, 
                 config_module: Any, 
                 demographic_manager: DemographicManager,
                 inheritance_manager: InheritanceManager, 
                 firm_system: FirmSystem,
                 settlement_system: ISettlementSystem, 
                 public_manager: IAssetRecoverySystem, 
                 logger: logging.Logger,
                 household_factory: IHouseholdFactory, # NOW MANDATORY
                 shareholder_registry: IShareholderRegistry = None,
                 hr_service: Optional[IHRService] = None,
                 tax_service: Optional[ITaxService] = None,
                 agent_registry: Optional[IAgentRegistry] = None):
        
        # ... assignments ...
        self.household_factory = household_factory # Direct assignment if needed by Manager, or just pass to BirthSystem
        
        self.birth_system = BirthSystem(
            ...,
            household_factory=household_factory
        )
```

### 3.2. Test Suite Refactoring

#### A. `tests/integration/test_wo167_grace_protocol.py`
- **Issue**: `TestGraceProtocol` instantiates `AgentLifecycleManager` with mock config but misses the factory.
- **Fix**:
    1.  Import `IHouseholdFactory` protocol.
    2.  Create `mock_factory = MagicMock(spec=IHouseholdFactory)`.
    3.  Pass `household_factory=mock_factory` to the constructor.

#### B. `tests/unit/test_lifecycle_reset.py`
- **Issue**: `TestLifecycleReset` fails to provide the factory.
- **Fix**: Same as above. Ensure `spec=IHouseholdFactory` is used to enforce protocol compliance during the test.

## 4. Verification Plan

### 4.1. Automated Tests
- [ ] **Unit Test**: Run `pytest tests/unit/test_lifecycle_reset.py` to confirm initialization passes.
- [ ] **Integration Test**: Run `pytest tests/integration/test_wo167_grace_protocol.py` to ensure Grace Protocol logic remains intact after DI change.

### 4.2. Cycle & Deprecation Check
- [ ] **Bootstrap Audit**: Verify `simulation/main.py` (or equivalent orchestrator) initializes components in this order:
    1.  `Config`
    2.  `SettlementSystem`
    3.  `DemographicManager`
    4.  `HouseholdFactory` (Depends on `Settlement`, `Demographic`)
    5.  `AgentLifecycleManager` (Depends on `HouseholdFactory`)
- [ ] **Deprecation**: Check logs for `Government.collect_tax` warnings. If found in `DeathSystem` or `LiquidationManager`, flag for future refactoring (out of scope for *this* hotfix, but note in Insight).

## 5. Mandatory Reporting & Insights
- **Requirement**: Create `communications/insights/spec-lifecycle-init-fix.md`.
- **Content**:
    - Confirm tests passed.
    - Document the explicit initialization order required for the Simulation Bootstrap (Resolves **TD-ARCH-DI-SETTLE** ambiguity).
    - Note any remaining "God Class" symptoms in `AgentLifecycleManager`.

## 6. Risk Assessment
- **High**: Changing the constructor signature is a breaking change. All instantiation points (prod code + tests) must be updated.
- **Mitigation**: `grep` the codebase for `AgentLifecycleManager(` to ensure no other call sites are missed.

---

**[Worker Note]**: Please execute the `grep` search for `AgentLifecycleManager(` immediately before applying changes to identify any other hidden dependencies.