# Technical Insight: Native IFinancialEntity Refactor

## 1. Problem Phenomenon
The financial system relied on `FinancialEntityAdapter` to bridge the gap between the `IFinancialEntity` interface and the heterogeneous implementations of agents (`Household`, `Firm`, `Bank`, `Government`). This introduced several issues:
- **Performance Overhead**: Every transaction required instantiating an adapter object.
- **Type Fragility**: The adapter used `hasattr` checks and `try-except` blocks to guess how to interact with an agent, leading to runtime fragility and masking potential interface violations.
- **Ambiguous Contracts**: The `IFinancialEntity` interface was effectively "optional" for agents, relying on the adapter to enforce it at runtime. This made it difficult to reason about agent capabilities statically.
- **Currency Confusion**: There were conflicting definitions of `IFinancialEntity` (single-currency vs multi-currency), and the adapter attempted to handle both, obscuring the intended single-currency semantics of the core settlement layer.

## 2. Root Cause Analysis
- **Legacy Evolution**: Agents evolved independently with different internal financial structures (`_econ_state.wallet`, `finance.balance`, `_wallet`).
- **Adapter Pattern Misuse**: The Adapter pattern was used as a permanent crutch rather than a temporary migration tool.
- **Lack of Interface Enforcement**: Python's dynamic nature allowed agents to "duck type" their way through the system without strictly adhering to a shared protocol.

## 3. Solution Implementation Details
The solution involves refactoring the core agents to **natively implement** the `IFinancialEntity` protocol.
- **Protocol Definition**: `IFinancialEntity` in `modules/finance/api.py` is redefined to enforce strict, single-currency semantics (`assets -> float`, `deposit(amount)`, `withdraw(amount)`).
- **Agent Refactoring**:
    - `Household`: Implements `IFinancialEntity`, exposing `assets` as a property returning `DEFAULT_CURRENCY` balance from its wallet.
    - `Firm`: Implements `IFinancialEntity`, delegating `deposit`/`withdraw` to its `FinanceDepartment`.
    - `Bank`: Implements `IFinancialEntity`, exposing its liquid reserves.
    - `Government`: Implements `IFinancialEntity`, exposing its treasury.
- **System Update**: `SettlementSystem` is updated to remove `FinancialEntityAdapter` and interact directly with agents via the strict interface.
- **Cleanup**: `FinancialEntityAdapter` is deleted.

## 4. Lessons Learned & Technical Debt
- **Strict Interfaces**: Enforcing protocols at the class level (even in Python) is crucial for large-scale simulations to ensure system integrity.
- **Zero-Sum Integrity**: Direct access to agent internals via the adapter was a risk. Native implementation allows agents to guard their state better (e.g., throwing `InsufficientFundsError` correctly).
- **Technical Debt**:
    - `Bank` and `Firm` internals are still multi-currency. The `IFinancialEntity` is a single-currency "view". Future refactoring might need to expose multi-currency capabilities more formally if cross-currency settlements become common.
    - `SettlementSystem`'s support for non-default currencies is now more limited (or requires agents to support it explicitly outside this interface). This simplifies the core loop but might restrict exotic transactions.
