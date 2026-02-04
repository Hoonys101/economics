# Spec: WO-4.2B - Orchestrator Alignment & Wallet Migration

- **Work Order**: WO-4.2B
- **Author**: Scribe (Gemini)
- **Status**: DRAFT
- **Risk Level**: HIGH
- **Related**: WO-4.2A (Wallet Abstraction), ARCH_SEQUENCING.md

---

## 1. Overview

This document outlines the specification for realigning the `TickOrchestrator` with the "Sacred Sequence" and completing the migration to a universal Wallet Abstraction Layer for all economic agents. This initiative addresses critical architectural debt identified in the `AUTO-AUDIT FINDINGS` for WO-4.2B.

The primary goals are:
1.  **Correct Sacred Sequence Violation**: Relocate monetary processing logic from the `TickOrchestrator`'s inter-phase hooks into a dedicated, correctly sequenced Phase.
2.  **Eliminate God Class Side-Effects**: Refactor the `Government` class by delegating all asset management to a new `Wallet` component, breaking up its monolithic state management.
3.  **Standardize Asset Access**: Mandate that all agents (`Firm`, `Household`, `Government`) interact with their assets exclusively through the new `IWallet` interface.
4.  **Preserve Zero-Sum Integrity**: Update and ensure the stability of the system's core Zero-Sum money supply verification mechanism throughout the transition.

## 2. Architectural Changes

### 2.1. TickOrchestrator & Phase Realignment

To enforce the "Sacred Sequence", the `TickOrchestrator` will be simplified, and all business logic will be moved into discrete phases.

#### **Phase Sequence Modification**

A new phase, `Phase_MonetaryProcessing`, will be introduced into the main sequence. This phase will be responsible for processing credit creation and destruction events. It will be placed *after* tax intents are generated and *before* final transaction settlements.

**Target `TickOrchestrator.phases` sequence:**

```python
# ... (existing phases)
Phase_TaxationIntents(world_state),
# [NEW] Phase_MonetaryProcessing will be inserted here
Phase3_Transaction(world_state),
# ... (subsequent phases)
```

#### **`_drain_and_sync_state` Cleanup**

The call to `government.process_monetary_transactions()` within `TickOrchestrator._drain_and_sync_state` will be **completely removed**. This method will revert to its sole responsibility of syncing DTO state back to the `WorldState` without triggering business logic.

### 2.2. Wallet Abstraction Layer (IWallet)

All economic agents will now manage their funds through a dedicated `Wallet` component.

-   **Composition**: `Government`, `Firm`, and `Household` classes will each receive a new mandatory instance variable: `self.wallet: IWallet`.
-   **Delegation**: All methods required by the `ICurrencyHolder` interface will be delegated from the agent to its `wallet` component.
-   **Asset Access**: All direct manipulation of `_assets` dictionaries is now prohibited. All financial operations (spending, receiving funds) **MUST** go through the `wallet.deposit()` and `wallet.withdraw()` methods.

### 2.3. Government "God Class" Decomposition

The `Government` class will be refactored into two distinct concerns: fiscal operations and monetary oversight.

1.  **Fiscal Wallet**: The `Government`'s direct asset management is replaced by its `self.wallet: IWallet` instance. Methods like `invest_infrastructure` will be updated as follows:

    -   **Before**: `self._internal_sub_assets(cost)`
    -   **After**: `self.wallet.withdraw(cost, currency, memo="Infrastructure Investment")`

2.  **Monetary Ledger**: A new component, `MonetaryLedger`, will be created and instantiated within the `Government`. This component will implement `IMonetaryLedger` and will be solely responsible for tracking the national money supply delta. The logic from the old `government.process_monetary_transactions` will move here.

## 3. Zero-Sum Verification Strategy

The integrity of the money supply check is paramount.

### 3.1. `world_state.calculate_total_money()`

This function will be rewritten. The new implementation will iterate through all agents in `world_state.agents.values()` and sum the balances by querying each agent's wallet.

**Pseudo-code for `calculate_total_money()`:**

```python
total_supply = defaultdict(float)
all_agents_and_systems = list(world_state.agents.values()) + [world_state.bank] # etc.

for entity in all_agents_and_systems:
    if isinstance(entity, ICurrencyHolder):
        balances = entity.get_assets_by_currency()
        for currency, amount in balances.items():
            total_supply[currency] += amount
return total_supply
```

### 3.2. `Government.get_monetary_delta()`

This method will be preserved but will now delegate its call to the new `MonetaryLedger` component. The `Phase_MonetaryProcessing` will be responsible for feeding the `MonetaryLedger` the relevant transactions for the tick, ensuring the delta calculation remains accurate.

## 4. Interface 명세 (API Definitions)

The following interfaces will be added to `modules/finance/api.py`.

```python
from __future__ import annotations
from typing import Protocol, Dict, List, runtime_checkable
from abc import abstractmethod

from modules.system.api import CurrencyCode, ICurrencyHolder
from simulation.models import Transaction

# =================================================================
# WO-4.2B: Wallet Abstraction Layer & Monetary Ledger
# =================================================================

@runtime_checkable
class IWallet(ICurrencyHolder, Protocol):
    """
    An interface for a dedicated Wallet component that manages an agent's assets.
    It encapsulates all logic for deposits, withdrawals, and balance checks,
    and fully implements the ICurrencyHolder interface.
    """

    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> float:
        """Returns the balance for a specific currency."""
        ...

    @abstractmethod
    def can_afford(self, amount: float, currency: CurrencyCode) -> bool:
        """Checks if the wallet contains at least the specified amount."""
        ...

    @abstractmethod
    def deposit(self, amount: float, currency: CurrencyCode, memo: str) -> None:
        """
        Increases the balance by a given amount.
        Must be an atomic operation.
        """
        ...

    @abstractmethod
    def withdraw(self, amount: float, currency: CurrencyCode, memo: str) -> None:
        """
        Decreases the balance by a given amount.
        Raises InsufficientFundsError if the balance is too low.
        Must be an atomic operation.
        """
        ...

    # get_assets_by_currency is inherited from ICurrencyHolder


class IMonetaryLedger(Protocol):
    """
    An interface for the Government's role in tracking money supply changes.
    This separates the responsibility of tracking national monetary aggregates
    from the Government's own fiscal wallet.
    """

    @abstractmethod
    def process_monetary_transactions(self, transactions: List[Transaction]) -> None:
        """
        Processes a list of transactions, updating internal counters for
        credit creation and destruction.
        """
        ...

    @abstractmethod
    def get_monetary_delta(self, currency: CurrencyCode) -> float:
        """
        Returns the net change in the money supply recorded during the current tick
        for a specific currency.
        """
        ...

    @abstractmethod
    def reset_tick_flow(self) -> None:
        """
        Resets the per-tick counters for money creation and destruction.
        """
        ...
```

## 5. 검증 계획 (Verification Plan)

1.  **Unit Tests**:
    -   A comprehensive test suite for the new `Wallet` implementation, covering deposits, withdrawals, error conditions (`InsufficientFundsError`), and currency management.
    -   Unit tests for the `MonetaryLedger` to verify correct delta calculation.
2.  **Integration Tests**:
    -   A new integration test to verify the `Phase_MonetaryProcessing` phase correctly calls the `MonetaryLedger` and updates the government's monetary delta.
    -   An integration test to confirm that `_drain_and_sync_state` no longer processes monetary transactions.
3.  **Regression Tests**:
    -   The primary `test_money_supply_zero_sum` test **MUST** be updated to use the new `calculate_total_money` logic and pass without error. This is the highest priority verification task.
    -   Existing tests for government spending (welfare, infrastructure) must be refactored to mock the `government.wallet` object and must continue to pass.

## 6. Mocking 가이드 (Mocking Guide)

-   When testing methods on `Government` or other agents that involve spending or receiving money, tests **MUST NOT** patch internal `_assets` dictionaries.
-   Tests **MUST** mock the `wallet` component.
-   **Example**: To test `invest_infrastructure`, use `mocker.patch.object(mock_government.wallet, 'withdraw')` and assert it was called with the correct arguments.

## 7. 🚨 Risk & Impact Audit (Mitigation Plan)

-   **Re: God Class (`government.py`)**: This risk is mitigated by the planned decomposition into `Wallet` (for fiscal state) and `MonetaryLedger` (for monetary policy state). The refactoring will be extensive but will follow the clear separation of concerns defined in this spec.
-   **Re: Zero-Sum Verification Integrity**: This risk is addressed by the detailed plan in Section 3. The `calculate_total_money` rewrite and the preservation of the `get_monetary_delta` logic via the `MonetaryLedger` are designed to maintain this critical diagnostic.
-   **Re: "Sacred Sequence" Violation**: This violation is directly corrected by removing logic from `_drain_and_sync_state` and creating the new `Phase_MonetaryProcessing`, as detailed in Section 2.1. This restores architectural integrity.
-   **Re: Dependency Management**: This risk is mitigated by enforcing a strict unidirectional dependency (`Agent -> Wallet`) and using delegation. The `Wallet` will have no knowledge of the agent that owns it, preventing circular references.
