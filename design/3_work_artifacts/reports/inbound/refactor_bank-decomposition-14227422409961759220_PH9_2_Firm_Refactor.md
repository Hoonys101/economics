# Technical Insight Report: Firm Orchestrator-Engine Refactor (PH9-2)

## 1. Problem Phenomenon
The `Firm` agent architecture had degraded into a tightly coupled "God Class" despite using "Department" components.
- **Symptoms**:
  - `HRDepartment`, `FinanceDepartment`, etc., held a reference to `self.firm`, accessing and modifying its state directly (e.g., `self.firm.capital_stock`).
  - Circular dependencies made testing isolated components impossible without mocking the entire `Firm`.
  - `IInventoryHandler` protocol was violated in `__init__` and `liquidate_assets` by directly manipulating `_inventory`.
  - Internal orders were executed via direct method calls on components, bypassing the event/command pattern.

## 2. Root Cause Analysis
- **Architectural Drift**: As documented in `ARCH_AGENTS.md`, the initial vision of stateless components was abandoned for a "Pragmatic Choice" of stateful components with parent pointers (`self.firm`). This was done to avoid passing large state objects.
- **Protocol Bypass**: Convenience led to direct dictionary access for inventory management, breaking the `IInventoryHandler` encapsulation.

## 3. Solution Implementation Details
The refactor aligned the `Firm` agent with the **Orchestrator-Engine Pattern**:

### 3.1. State Extraction
- Created mutable dataclasses in `simulation/components/state/firm_state_models.py`:
  - `HRState`: Employees, wages.
  - `FinanceState`: Financial metrics, profit history, shares.
  - `ProductionState`: Capital stock, production target, specialization.
  - `SalesState`: Marketing budget, pricing history.
- `Firm` now holds these state objects as attributes.

### 3.2. Stateless Engines
- Created stateless engine classes in `simulation/components/engines/`:
  - `HREngine`, `FinanceEngine`, `ProductionEngine`, `SalesEngine`.
- Engines accept State objects and dependencies (Wallet, Config, MarketContext) as arguments.
- Engines do **not** hold a reference to `Firm`. They operate on the passed State.

### 3.3. Command Bus
- Refactored `_execute_internal_order` in `Firm` to act as a Command Bus.
- Internal orders (e.g., `SET_TARGET`, `INVEST_AUTOMATION`) are routed to the appropriate Engine method.

### 3.4. Strict Protocols
- `Firm` now strictly adheres to `IInventoryHandler`.
- `__init__` uses `add_item`.
- `liquidate_assets` uses `remove_item` (iterating over keys).

## 4. Lessons Learned & Technical Debt
- **Lesson**: Decoupling logic from state (Stateless Engines) makes the data flow explicit and testable. The "State" objects act as a clear contract of what data an engine needs.
- **Technical Debt Identified**:
  - **BaseAgent Property Mocking**: Testing `Firm` required complex patching of `BaseAgent` properties (`wallet`), indicating inheritance creates testing friction. Composition (Strategy pattern) might be better than inheritance for Agents.
  - **OrderDTO Ambiguity**: The codebase aliases `Order` to `OrderDTO` but uses `order_type` property which maps to `side`. This caused confusion in tests. Standardization on `OrderDTO` fields is recommended.
  - **Proxy Compatibility**: `HRProxy` and `FinanceProxy` were added to `Firm` to maintain backward compatibility for any external access (e.g., `firm.hr.employees`). These should be deprecated and removed in future phases.