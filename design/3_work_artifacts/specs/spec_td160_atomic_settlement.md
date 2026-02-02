# Specification: TD-160 & TD-187 - Atomic Estate and Severance Settlement

## 1. Problem Definition

- **ID**: TD-160, TD-187
- **Description**: The inheritance (`InheritanceManager`) and severance pay processes are not atomic. They generate a sequence of discrete `Transaction` objects, which can lead to partial execution if one step fails.
- **Root Cause**: The system lacks a mechanism to group related financial operations into a single, all-or-nothing transaction. The `InheritanceManager`'s direct, sequential creation of `Transaction` objects for liquidation, taxation, and distribution is an implicit, fragile attempt at a multi-step process.
- **Impact**:
    - **TD-160 (Money Leaks)**: If an estate is partially liquidated but the tax or distribution transaction fails, the assets of the deceased agent are left in a corrupted, intermediate state, effectively destroying wealth from the simulation (a "money leak").
    - **TD-187 (Race Condition)**: During firm liquidation, a timing issue between calculating available funds and paying severance can lead to over-withdrawal if assets are otherwise claimed, breaking the simulation's zero-sum integrity.

## 2. Detailed Implementation Plan

This refactoring will replace the sequential transaction generation with a Saga pattern, orchestrated by a new `SettlementSystem` that guarantees atomicity.

### Step 1: Define the Settlement Saga DTOs

In a new file, `simulation/dtos/settlement_dtos.py`, define the data contracts for our sagas.

```python
# simulation/dtos/settlement_dtos.py
from typing import List, Dict, Any, Literal
from dataclasses import dataclass, field

@dataclass
class EstateValuationDTO:
    """A read-only snapshot of the deceased's wealth."""
    cash: float
    real_estate_value: float
    stock_value: float
    total_wealth: float
    tax_due: float
    stock_holdings: Dict[int, float] # {firm_id: quantity}
    property_holdings: List[int] # [property_id]

@dataclass
class EstateSettlementSaga:
    """The complete, atomic unit of work for settling an estate."""
    saga_type: Literal["ESTATE_SETTLEMENT"] = "ESTATE_SETTLEMENT"
    deceased_id: int
    heir_ids: List[int]
    government_id: int
    valuation: EstateValuationDTO
    current_tick: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

### Step 2: Refactor `InheritanceManager`

The `InheritanceManager` will be simplified into a read-only valuation and saga creation service. It will no longer create `Transaction` objects.

- **Modify `simulation/systems/inheritance_manager.py`**:
    - The `process_death` method signature will change to `def process_death(...) -> EstateSettlementSaga:`.
    - The method will perform all the valuation steps as before (calculating cash, stock value, RE value, tax).
    - Instead of creating a list of `Transaction`s, it will populate and return a single `EstateSettlementSaga` object.
    - It will no longer need write-access to any part of the simulation state.

### Step 3: Create the `SettlementSystem` and Saga Handler

A new system will be responsible for executing these sagas atomically.

- **Create `simulation/systems/settlement_system.py`**:
    - The `SettlementSystem` will have a method `submit_saga(saga: EstateSettlementSaga)`.
    - Internally, it will have a registry of handlers: `self.handlers = {"ESTATE_SETTLEMENT": self.handle_estate_settlement}`.
    - The `execute` method of the system will process its queue of submitted sagas.

- **Implement the Saga Handler (`handle_estate_settlement`)**:
    - This method receives the `EstateSettlementSaga` DTO.
    - It will perform the settlement as a **single, ACID-compliant operation**.
    - **Execution Steps & Compensation (Rollback) Logic**:
        1.  **BEGIN TRANSACTION** (Conceptually).
        2.  **Freeze Deceased's Accounts**: No further direct debits/credits allowed.
        3.  **Liquidate Assets (if cash < tax)**:
            - **Action**: Debit stocks/property from deceased portfolio, credit to government portfolio.
            - **Action**: Credit deceased's cash account with sale value.
            - **Compensation**: Reverse the transfers.
        4.  **Pay Inheritance Tax**:
            - **Action**: Debit `tax_due` from deceased's cash, credit government cash.
            - **Compensation**: Reverse the transfer. If this step fails, **the entire saga rolls back**.
        5.  **Distribute Inheritance / Escheat**:
            - **Action (Heirs)**: Debit remaining cash from deceased, credit to heirs' accounts (split evenly).
            - **Action (Escheat)**: Debit all remaining assets (cash, stocks, property if not liquidated) from deceased, credit to government.
            - **Compensation**: Reverse the transfers.
        6.  **COMMIT TRANSACTION** (Conceptually). Mark saga as complete.

### Step 4: Integrate `SettlementSystem` into the Simulation Loop

- In `WorldState`, initialize `self.settlement_system = SettlementSystem(...)`.
- The phase responsible for lifecycle/death (e.g., `Phase_Bankruptcy`) will now:
    1.  Call `InheritanceManager.process_death()` for each deceased agent.
    2.  Receive the `EstateSettlementSaga` object.
    3.  Submit it to `world_state.settlement_system`.
- A new phase, `Phase_Settlement`, will be added to `TickOrchestrator`'s phase list, running after decisions but before transaction processing, to execute the sagas.

## 3. Verification Criteria

1.  **New Unit Tests for `SettlementSystem`**:
    - `tests/systems/test_settlement_system.py`:
        - Test successful inheritance with and without liquidation.
        - Test successful escheatment.
        - **Crucially, test the rollback mechanism**: Create a scenario where the deceased has valuable assets but not enough cash is raised during liquidation to pay the full tax. Verify that the saga fails and the assets (stocks, properties) are returned to the deceased's (frozen) portfolio, and no cash has been transferred to the government.

2.  **Zero-Sum Conservation Test**:
    - An integration test will be written that tracks total money supply and total assets (stocks, properties) in the simulation.
    - It will trigger an inheritance event and assert that the total value of all assets and money in the simulation remains constant before and after the `SettlementSystem` runs (i.e., assets are only transferred, not created or destroyed).

3.  **Refactoring Verification**:
    - The `InheritanceManager.process_death` method should no longer return a `List[Transaction]`.
    - No `Transaction` objects with `transaction_type` of `inheritance_distribution`, `escheatment`, or `asset_liquidation` should be generated anywhere outside the `SettlementSystem`.
