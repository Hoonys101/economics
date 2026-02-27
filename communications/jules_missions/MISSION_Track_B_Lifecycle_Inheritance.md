# MISSION: Track B - Agent Lifecycle & Estate Management
# Role: Jules (Legacy Systems Architect)

## Objective
Ensure that dying agents' assets are fully distributed or escheated without leaving "ghost money" in the simulation.

## Scope
- `simulation/systems/lifecycle/death_system.py`
- `simulation/systems/inheritance_manager.py`
- `simulation/systems/handlers/inheritance_handler.py`
- `simulation/systems/handlers/escheatment_handler.py`

## Specific Tasks
1. **SSoT Inheritance**: Update `InheritanceHandler` to use the base `total_pennies` calculated by the `InheritanceManager` to avoid leaks from shared wallets.
2. **Atomic Settlement**: Verify that all heir distributions occur within a single `settle_atomic` call.
3. **Registry Integrity**: Ensure the `EstateRegistry` (Graveyard) is updated *only* after successful financial settlement.
4. **Rollback Logic**: Implement and test double-entry rollbacks for failed inheritance transactions.

## Success Criteria
- No `ID_ESCROW` leaks detected in `EstateRegistry`.
- `test_inheritance_manager.py` passes with zero warnings.
