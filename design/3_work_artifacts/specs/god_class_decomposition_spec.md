# Spec: God Class Decomposition (Firm & Household)

**Mission Key**: `firm-household-decomp-spec`
**Status**: DRAFT
**Owner**: Gemini (Scribe)
**Target Phase**: Phase 16.1 (Lane 3)

## 1. Executive Summary

The `Firm` and `Household` classes have accumulated excessive responsibilities, acting as "God Orchestrators" that directly manage state, implement numerous protocols, and orchestrate complex engine pipelines. This specification outlines a structural refactoring using the **Component-Entity-System (CES) Lite** pattern to reduce code volume, improve testability, and enforce strict separation of concerns without altering public APIs.

## 2. Problem Statement

1.  **Protocol Bloat**: `Firm` implements 10+ interfaces directly (`IInventoryHandler`, `IFinancialAgent`, etc.), resulting in hundreds of lines of getter/setter boilerplate.
2.  **State Exposure**: Internal state (e.g., `_inventory`, `_wallet`) is manipulated directly by the Agent, bypassing encapsulation and making it hard to enforce invariants (e.g., negative inventory checks).
3.  **Orchestration Coupling**: Complex methods like `generate_transactions` (Firm) and `update_needs` (Household) mix logic with orchestration, making them hard to unit test without full agent instantiation.
4.  **Testing Fragility**: Tests rely on mocking the entire Agent, leading to "Mock Hell" when internal implementations change.

## 3. Solution Architecture: Agent Shell Pattern

We will transform `Firm` and `Household` into **Agent Shells**. A Shell is a lightweight container that:
1.  **Holds Components**: Owns `InventoryComponent`, `FinancialComponent`, etc.
2.  **Delegates Protocols**: Implements public interfaces by forwarding calls to components.
3.  **Orchestrates Engines**: Uses `TransactionOrchestrator` to wire stateless engines together.

### 3.1. New Components (`modules/agent_framework/components/`)

#### A. `InventoryComponent`
-   **Responsibility**: Manages `main` and `input` inventory slots, quality tracking, and serialization.
-   **Implements**: `IInventoryHandler`, `IInventoryComponent`.
-   **State**: Holds `InventoryStateDTO`.

#### B. `FinancialComponent`
-   **Responsibility**: Wraps `Wallet`, enforces `IFinancialEntity` (Penny Standard), tracks `credit_frozen` state.
-   **Implements**: `IFinancialEntity`, `ICreditFrozen`, `IFinancialComponent`.
-   **State**: Holds `Wallet` instance.

#### C. `FirmTransactionOrchestrator` (Service)
-   **Responsibility**: Encapsulates the `generate_transactions` pipeline.
-   **Input**: `FirmStateDTO`, `FiscalContext`, `MarketContext`.
-   **Output**: `List[Transaction]`.
-   **Logic**: Calls `HREngine`, `FinanceEngine`, `SalesEngine` in sequence.

### 3.2. Refactored Agent Structure (Pseudo-Code)

```python
class Firm(ILearningAgent, IFinancialFirm, ...):
    def __init__(self, ...):
        # Composition
        self.inventory_comp = InventoryComponent()
        self.financial_comp = FinancialComponent()
        self.txn_orchestrator = FirmTransactionOrchestrator()

        # ... Engines ...

    # Protocol Delegation (Boilerplate Reducer)
    @property
    def inventory(self): return self.inventory_comp.get_all_items()

    def add_item(self, *args): return self.inventory_comp.add_item(*args)

    @property
    def balance_pennies(self): return self.financial_comp.balance_pennies

    # Simplified Orchestration
    def generate_transactions(self, ...):
        # Delegate complex wiring to the orchestrator
        return self.txn_orchestrator.orchestrate(
            state=self.get_snapshot_dto(),
            engines=(self.hr_engine, self.finance_engine, self.sales_engine),
            context=...
        )
```

## 4. Implementation Plan (Parallel Lane 3)

This work is assigned to **Lane 3** of the Parallel Technical Debt Clearance Strategy.

### Step 1: Component Creation (Safe)
-   Create `modules/agent_framework/components/inventory_component.py`.
-   Create `modules/agent_framework/components/financial_component.py`.
-   Create `modules/firm/orchestrators/transaction_orchestrator.py`.
-   **Verification**: Unit test components in isolation.

### Step 2: Firm Refactoring (Lane 3A)
-   Replace `Firm._inventory` with `Firm.inventory_comp`.
-   Replace `Firm._wallet` usage with `Firm.financial_comp`.
-   Delegate protocol methods.
-   **Verification**: Run `tests/simulation/agents/test_firm.py` (Must pass without modification to tests).

### Step 3: Household Refactoring (Lane 3B)
-   Follow similar pattern for `Household`.
-   Extract `HouseholdLifecycleOrchestrator` to handle the `update_needs` pipeline.
-   **Verification**: Run `tests/simulation/agents/test_household.py`.

## 5. Verification Strategy

### 5.1. Component Tests
-   **Test**: `tests/modules/agent_framework/test_inventory_component.py`
-   **Scenario**: Add item, Remove item, Check Quality, Snapshot/Restore.
-   **Success**: 100% logic coverage of inventory math.

### 5.2. Integration Tests (Regression)
-   **Test**: `tests/simulation/agents/test_firm_decomposition.py`
-   **Scenario**:
    1.  Instantiate Refactored Firm.
    2.  Perform `add_item`.
    3.  Verify item is in `firm.inventory_comp`.
    4.  Verify `firm.get_quantity()` returns correct value.
    5.  Run full `make_decision` cycle to ensure orchestration wiring holds.

## 6. Risk Analysis

-   **Risk**: `load_state` / `get_current_state` logic drift.
    -   *Mitigation*: The `Component` must provide `to_dto()` and `from_dto()` methods. The Agent's `load_state` must explicitly call these.
-   **Risk**: Performance overhead of delegation.
    -   *Mitigation*: Python method calls are cheap enough for this simulation scale. The structural clarity outweighs micro-optimization.
-   **Risk**: Circular Imports.
    -   *Mitigation*: Components must NOT import the Agent class. They only import DTOs and Protocols.

## 7. Mandatory Reporting Instruction

**[INSTRUCTION FOR ASSIGNED AGENT]**
Upon drafting this spec, you MUST create the insight report at `communications/insights/firm-household-decomp-spec.md` with the following content:
1.  Confirmation of Decomposition Strategy (CES Lite).
2.  List of created Component Interfaces.
3.  Verification that this approach adheres to SEO Pattern (Components are stateful helpers, Engines remain stateless).
