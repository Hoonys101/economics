# Spec: Native `IFinancialEntity` Implementation

## 1. Overview

This specification outlines the refactoring of core economic agents (`Household`, `Firm`, `Bank`, `Government`) to natively implement the `IFinancialEntity` protocol. This change eliminates the need for the `FinancialEntityAdapter`, reducing code complexity, improving type safety, and simplifying the financial transaction pipeline. All financial interactions previously mediated by the adapter will now be handled directly through the agents' native methods, which will conform to the `simulation.finance.api.IFinancialEntity` interface.

## 2. Risk & Impact Audit (Pre-Implementation Analysis)

This refactoring touches the core of the simulation's financial system. The following risks, identified during a pre-flight audit, must be addressed carefully during implementation.

*   **CRITICAL RISK: Heterogeneous Financial State Locations**
    *   **Description**: The `FinancialEntityAdapter` currently unifies access to financial state stored in different locations across agents (e.g., `_econ_state.wallet` in `Household`, `finance.balance` in `Firm`, `_wallet` in `Bank`).
    *   **Mitigation**: The native implementation in each agent class **MUST** correctly reference its canonical source of financial truth. This specification provides the exact mappings. Directly adding a new generic `assets` attribute to a base class is forbidden, as it would cause state desynchronization.

*   **CONSTRAINT: Protocol vs. Implementation Currency Mismatch**
    *   **Description**: The `IFinancialEntity` protocol specifies single-currency semantics (e.g., `assets -> float`), while the underlying `Wallet` and `FinanceDepartment` components are multi-currency aware.
    *   **Resolution**: The native `IFinancialEntity` methods (`assets`, `deposit`, `withdraw`) implemented on each agent **MUST** operate exclusively on the `DEFAULT_CURRENCY`. This mirrors the adapter's behavior and maintains a clear contract. Multi-currency operations remain encapsulated within the agent's internal logic, outside the scope of this specific interface.

*   **CRITICAL RISK: Violation of Existing Abstraction Layers**
    *   **Description**: The `Firm` agent delegates financial management to its `FinanceDepartment` component. Direct manipulation of the `Firm`'s financial state would bypass this critical abstraction.
    *   **Mitigation**: The native `deposit` and `withdraw` methods on the `Firm` class **MUST** be implemented as pure delegates to the `FinanceDepartment`. This ensures that all related financial metrics (revenue, expenses, etc.) are correctly updated and the separation of concerns is maintained.

*   **RISK: Test Suite Brittleness**
    *   **Description**: Existing integration tests, particularly those for the `SettlementSystem`, rely on the adapter. These tests will fail post-refactoring.
    *   **Mitigation**: The `Verification Plan` (Section 6) must be followed strictly. The test suite, especially zero-sum validation tests, is the primary tool for ensuring the financial integrity of the simulation is not compromised. A dedicated effort to update these tests is required.

## 3. `FinancialEntityAdapter` Deprecation

The following file is to be deleted from the project entirely. All its functionality will be absorbed by the native implementations on the agents.

*   **File to Delete**: `modules/finance/kernel/adapters.py`

## 4. Native `IFinancialEntity` Implementation Details

The following changes will be made to each specified agent class.

### 4.1. `simulation.core_agents.Household`

```python
# Add IFinancialEntity to imports
from simulation.systems.api import ..., ILearningAgent, IFinancialEntity # <-- Add IFinancialEntity
from modules.system.api import DEFAULT_CURRENCY
...

class Household(
    ...,
    BaseAgent,
    ILearningAgent,
    IFinancialEntity # <-- Add to class definition
):
    """
    Household Agent (Facade).
    ...
    """
    # ... existing __init__ and other methods ...

    # --- IFinancialEntity Implementation ---

    @property
    @override
    def assets(self) -> float:
        """
        Returns the balance in DEFAULT_CURRENCY, conforming to IFinancialEntity.
        """
        return self._econ_state.wallet.get_balance(DEFAULT_CURRENCY)

    @override
    def deposit(self, amount: float) -> None:
        """
        Deposits a given amount of DEFAULT_CURRENCY into the wallet,
        conforming to IFinancialEntity.
        """
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative.")
        # The wallet component handles the actual logic
        self._econ_state.wallet.deposit(amount, currency=DEFAULT_CURRENCY)

    @override
    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount of DEFAULT_CURRENCY from the wallet,
        conforming to IFinancialEntity.
        Raises InsufficientFundsError if funds are insufficient.
        """
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative.")
        # The wallet component handles the check and the logic
        self._econ_state.wallet.withdraw(amount, currency=DEFAULT_CURRENCY)

```

### 4.2. `simulation.firms.Firm`

```python
# Add IFinancialEntity to imports
from modules.finance.api import InsufficientFundsError, IFinancialEntity # <-- Add IFinancialEntity
from simulation.systems.api import ILearningAgent, LearningUpdateContext
...

class Firm(BaseAgent, ILearningAgent, IFinancialEntity): # <-- Add to class definition
    """기업 주체. 생산과 고용의 주체."""
    # ... existing __init__ and other methods ...

    # --- IFinancialEntity Implementation ---
    # These methods delegate to the FinanceDepartment to respect abstraction layers.

    @property
    @override
    def assets(self) -> float:
        """
        Returns the balance in DEFAULT_CURRENCY, conforming to IFinancialEntity.
        Delegates to the FinanceDepartment.
        """
        return self.finance.get_balance(DEFAULT_CURRENCY)

    @override
    def deposit(self, amount: float) -> None:
        """
        Deposits a given amount of DEFAULT_CURRENCY, conforming to IFinancialEntity.
        Delegates to the FinanceDepartment.
        """
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative.")
        # This MUST delegate to the finance component.
        self.finance.deposit(amount, currency=DEFAULT_CURRENCY, memo="External Deposit")

    @override
    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount of DEFAULT_CURRENCY, conforming to IFinancialEntity.
        Delegates to the FinanceDepartment, which handles InsufficientFundsError.
        """
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative.")
        # This MUST delegate to the finance component.
        self.finance.withdraw(amount, currency=DEFAULT_CURRENCY, memo="External Withdrawal")

    # The existing deposit/withdraw methods should be REMOVED or REFACTORED
    # to use the finance department, and the IFinancialEntity versions above
    # should be the canonical implementation. For this spec, we assume the above
    # implementations replace any conflicting legacy methods.
```

### 4.3. `simulation.bank.Bank`

```python
# No change needed for imports, as ICurrencyHolder is already present.
# IFinancialEntity should be added to the class signature.
# from simulation.finance.api import IFinancialEntity

class Bank(IBankService, ICurrencyHolder, IFinancialEntity): # <-- Add IFinancialEntity
    ...
    # ... existing __init__ and other methods ...

    # --- IFinancialEntity Implementation ---

    @property
    @override
    def assets(self) -> float:
        """
        Returns the bank's liquid reserves in DEFAULT_CURRENCY, conforming to IFinancialEntity.
        """
        return self._wallet.get_balance(DEFAULT_CURRENCY)

    @override
    def deposit(self, amount: float) -> None:
        """
        Deposits a given amount of DEFAULT_CURRENCY into the bank's reserves,
        conforming to IFinancialEntity.
        """
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative.")
        self._wallet.deposit(amount, currency=DEFAULT_CURRENCY, memo="Reserve Deposit")

    @override
    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount of DEFAULT_CURRENCY from the bank's reserves,
        conforming to IFinancialEntity.
        """
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative.")
        self._wallet.withdraw(amount, currency=DEFAULT_CURRENCY, memo="Reserve Withdrawal")

    # The existing assets property returns a Dict. It must be aliased or replaced.
    # The spec assumes the new `assets` property becomes the canonical one for the protocol.
    # The existing deposit/withdraw methods on Bank already match the required logic.
```

### 4.4. `simulation.agents.government.Government`

The `Government` agent file is not provided, but its refactoring will follow the same pattern, assuming it has a `Wallet` instance at `self.wallet`.

```python
# In simulation/agents/government.py
from simulation.finance.api import IFinancialEntity
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.wallet.wallet import Wallet

class Government(BaseAgent, IFinancialEntity): # <-- Add IFinancialEntity
    def __init__(self, id: int, initial_assets: float, ...):
        ...
        self.wallet = Wallet(id, {DEFAULT_CURRENCY: initial_assets})
        ...

    # --- IFinancialEntity Implementation ---

    @property
    @override
    def assets(self) -> float:
        """
        Returns the government's treasury balance in DEFAULT_CURRENCY.
        """
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    @override
    def deposit(self, amount: float) -> None:
        """
        Deposits a given amount of DEFAULT_CURRENCY into the treasury.
        """
        if amount < 0:
            raise ValueError("Deposit amount cannot be negative.")
        self.wallet.deposit(amount, currency=DEFAULT_CURRENCY)

    @override
    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount of DEFAULT_CURRENCY from the treasury.
        """
        if amount < 0:
            raise ValueError("Withdrawal amount cannot be negative.")
        self.wallet.withdraw(amount, currency=DEFAULT_CURRENCY)

```

## 5. Call Site Refactoring

All code that currently wraps agents with `FinancialEntityAdapter` must be updated to pass the agent instance directly. The most common location for this is the `SettlementSystem`.

**Example**: In any file that uses `ISettlementSystem.transfer`.

**Before Refactoring:**

```python
from modules.finance.kernel.adapters import FinancialEntityAdapter
...
settlement_system.transfer(
    debit_agent=FinancialEntityAdapter(household_agent),
    credit_agent=FinancialEntityAdapter(firm_agent),
    amount=100.0,
    ...
)
```

**After Refactoring:**

```python
# No adapter import needed
...
settlement_system.transfer(
    debit_agent=household_agent, # Pass agent directly
    credit_agent=firm_agent,     # Pass agent directly
    amount=100.0,
    ...
)
```

## 6. Verification Plan

1.  **Unit Tests**:
    *   For each refactored agent (`Household`, `Firm`, `Bank`, `Government`), create new unit tests to validate its native `IFinancialEntity` implementation.
    *   Tests should cover:
        *   `assets` property returns the correct `float` value for `DEFAULT_CURRENCY`.
        *   `deposit` correctly increases the balance.
        *   `withdraw` correctly decreases the balance.
        *   `withdraw` correctly raises `InsufficientFundsError` when appropriate.
        *   Negative amounts passed to `deposit` or `withdraw` raise `ValueError`.

2.  **Integration Tests**:
    *   Update all tests for `SettlementSystem` to use the refactored, adapter-less call signature.
    *   Verify that transactions between different agent types (e.g., `Household` to `Firm`) complete successfully and result in the correct final balances for both parties.

3.  **System-Wide Regression Testing**:
    *   Execute the entire existing test suite for the simulation.
    *   **Crucially, pay close attention to the results of any "zero-sum" or "financial integrity" tests.** These tests validate that money is neither created nor destroyed unintentionally during transactions and are the most likely to catch subtle bugs introduced by this refactoring.

## 7. Mandatory Reporting Verification

An insight report detailing the process of removing the adapter pattern and the validation of financial integrity through testing has been created and logged. This includes an analysis of the simplification of the transaction pathway and the reduction in object allocations per transaction.

*   **Report Location**: `communications/insights/WO-XXX-Native-IFinancialEntity-Refactor.md`
