# Mission Guide: Lifecycle Manager Decomposition

## 1. Objectives (TD-ARCH-LIFE-GOD)
- **Decompose the Monolith**: Split `LifecycleManager` into discrete, testable systems: `BirthSystem`, `DeathSystem`, `AgingSystem`.
- **Stateless Orchestration**: Transition the manager to a coordinator that invokes these sub-systems.
- **Improved Testability**: Enable unit testing of "Death" logic (e.g., bankruptcy liquidation) without full agent instantiation dependencies.

## 2. Reference Context (MUST READ)
### Primary Target
- [lifecycle_manager.py](../../../simulation/systems/lifecycle_manager.py)

### Secondary Context (Integration points)
- [main.py](../../../main.py) (Where lifecycle is invoked)
- [welfare_service.py](../../../modules/government/services/welfare_service.py) (Interacts with survival/liquidation)

## 3. Implementation Roadmap
### Phase 1: Structural Design
- Analyze `LifecycleManager` and extract methods into separate classes in `simulation/systems/lifecycle/`.
- Ensure sub-systems are stateless (Engine-style) or have clear state ownership.

### Phase 2: Implementation Spec
- Draft the new directory structure and class signatures.
- Define a unified `ILifecycleStep` protocol if applicable.

### Phase 3: Migration & Verification
- Update `main.py` entry point.
- Verify agent birth/death cycles remain stable.

## 4. Success Criteria
- `LifecycleManager` reduced by >60% in line count.
- All lifecycle-related tests pass.
- No regression in agent population stability.
