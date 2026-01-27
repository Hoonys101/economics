# Work Order: WO-124 Genesis Fix (Jules-Go)

## 1. Directive
Implement the **Genesis Protocol (Sacred Sequence)** as defined in `design/specs/WO-124_GENESIS_FIX_SPEC.md`. This is a critical mission to stop the Tick 1 asset leak (TD-115) and restore architectural purity (TD-117).

## 2. Tasks

### Task 1: Refactor `SimulationInitializer` (Genesis Protocol)
- **File**: `simulation/initialization/initializer.py`
- **Logic**:
    1.  Initialize `CentralBank` early.
    2.  Mint `CONFIG.INITIAL_MONEY_SUPPLY` into the `CentralBank` (via `deposit` or a new `mint` method).
    3.  Ensure all Agents are created with **0.0 starting assets**.
    4.  Call `Bootstrapper` to distribute funds using `SettlementSystem.transfer(central_bank, ...)`.
    5.  Set `sim.world_state.baseline_money_supply` **after** this distribution.

### Task 2: Standardize `Bootstrapper`
- **File**: `simulation/systems/bootstrapper.py`
- **Logic**: 
    - Change `inject_initial_liquidity` to use `settlement_system.transfer` from the Central Bank.
    - Remove all direct property mutations of `assets`.

### Task 3: WorldState Integrity
- **File**: `simulation/world_state.py`
- **Logic**: 
    - Ensure `calculate_total_money` includes the `CentralBank` cash balance to maintain zero-sum integrity against the minted M0.

### Task 4: Trace & Verify
- **Activity**: Run a 1-tick simulation.
- **Goal**: `Initial baseline money supply established` log must match `INITIAL_MONEY_SUPPLY`. `Delta` at Tick 1 must be `0.00`.

## 3. Mission Status
- **Priority**: CRITICAL
- **Spec**: `design/specs/WO-124_GENESIS_FIX_SPEC.md`
- **Target Debt**: TD-115, TD-117

---

## 🚀 Execution (Jules-Go Template)
To execute this work order, run:
`python scripts/jules/dispatch.py --work-order design/work_orders/WO-124_JULES_GO.md`
