# [Spec] Engine Decoupling: Protocol-Driven Refactoring

**ID:** TDR-001
**Author:** Scribe (Gemini)
**Source Audit:** `STRUCTURAL-002`, `TDL-PH9-2-STRUCTURAL`
**Date:** 2026-02-08

## 1. Overview

This document outlines the technical specification for refactoring the `HREngine`, `FinanceEngine`, and `SalesEngine` to eliminate critical abstraction leaks. As identified in audit `STRUCTURAL-002`, these core engines currently accept raw agent objects (`agent`, `government`, `household`), creating tight coupling, violating the Purity Gates principle, and severely hindering isolated unit testing.

The goal is to replace these concrete dependencies with granular, role-based Protocols and DTOs. This will decouple the stateless engine logic from the agent implementations, making the engines 100% testable in isolation and mitigating the "Near God Class" risk in `firm.py` and `government.py`.

## 2. Prerequisite: `ISettlementSystem` Refactoring

The successful decoupling of the engines is **blocked** by the current `ISettlementSystem.transfer` signature, which requires a full `agent: IFinancialEntity` object. To proceed, `ISettlementSystem` must be evolved to handle transactions via identifiers and wallets, removing the need for the caller to provide the full agent object.

**Proposed New `ISettlementSystem` Methods:**

```python
class ISettlementSystem(Protocol):
    # ... existing methods ...

    def transfer(
        self,
        payer: IFinancialEntity,
        payee: IFinancialEntity,
        # ...
    ) -> bool: ...

    # PROPOSED NEW METHOD
    def transfer_from_wallet(
        self,
        payer_wallet: IWallet,
        payer_id: int, # For logging/transaction record
        payee_id: int,
        amount: float,
        memo: str,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> bool:
        """
        Executes a transfer using wallet objects and agent IDs,
        removing the need for full agent instances.
        The system will use the IDs to look up the payee's wallet.
        """
        ...
```

**All subsequent sections assume this prerequisite is met.** Engine methods requiring transfers will be updated to use `transfer_from_wallet`.

## 3. API Definitions (`modules/simulation/api.py`)

The following new protocols and DTOs shall be defined in `modules/simulation/api.py` to serve as the clean, decoupled interfaces for the engines.

```python
# In modules/simulation/api.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, TypedDict, Any, List, Dict, Optional, TYPE_CHECKING, runtime_checkable

# ... existing imports ...
from modules.finance.wallet.api import IWallet

# --- New Granular Protocols ---

@runtime_checkable
class ITransactionalEntity(Protocol):
    """Represents any entity that can be a party in a transaction, identified by an ID."""
    @property
    def id(self) -> int: ...


@runtime_checkable
class ITaxAuthority(ITransactionalEntity, Protocol):
    """Defines the interface for a government entity providing tax calculation services."""

    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """Calculates the cost of survival for tax exemption purposes."""
        ...

    def calculate_income_tax(self, gross_income: float, survival_cost: float) -> float:
        """Calculates the income tax based on gross income."""
        ...


@runtime_checkable
class IShareholderRegistryView(Protocol):
    """A read-only interface for accessing shareholder information."""

    def get_shareholders_of_firm(self, firm_id: int) -> List[Dict[str, Any]]:
        """Returns a list of shareholders for a given firm."""
        ...


# --- New DTOs for Engine Payloads ---

@dataclass(frozen=True)
class PayrollProcessingContext:
    """
    Immutable context bundle for the HREngine.process_payroll method.
    Contains all external dependencies required for payroll calculation.
    """
    firm_id: int
    firm_wallet: IWallet
    firm_config: "FirmConfigDTO"
    current_time: int
    market_context: "MarketContextDTO"
    tax_authority: Optional[ITaxAuthority]
    # DEPRECATES `government`
    # DEPRECATES `finance_engine_helper`


@dataclass(frozen=True)
class FinancialTransactionContext:
    """
    Immutable context for FinanceEngine.generate_financial_transactions.
    """
    firm_id: int
    firm_wallet: IWallet
    firm_config: "FirmConfigDTO"
    current_time: int
    market_context: "MarketContextDTO"
    inventory_value: float
    shareholder_view: IShareholderRegistryView
    fee_recipient: ITransactionalEntity # Typically the government
    # DEPRECATES `government`
    # DEPRECATES `shareholder_registry`

@dataclass(frozen=True)
class InvestmentContext:
    """
    Immutable context for executing an investment.
    """
    firm_id: int
    firm_wallet: IWallet
    amount: float
    recipient: ITransactionalEntity # e.g., Government for R&D
    settlement_system: "ISettlementSystem"
    memo: str
    # DEPRECATES `agent`, `government`

```

## 4. Engine Method Refactoring

### 4.1. HREngine (`simulation/components/engines/hr_engine.py`)

#### `process_payroll`
- **Reasoning:** Decouples payroll logic from the concrete `Government` and `Firm` implementations. `PayrollProcessingContext` bundles all dependencies into a single, clean DTO.
- **Before:**
  ```python
  def process_payroll(
      self,
      hr_state: HRState,
      firm_id: int,
      wallet: IWallet,
      config: FirmConfigDTO,
      current_time: int,
      government: Optional[Any],
      market_data: Optional[Dict[str, Any]],
      market_context: MarketContextDTO,
      finance_engine_helper: Any = None
  ) -> List[Transaction]: ...
  ```
- **After:**
  ```python
  def process_payroll(
      self,
      hr_state: HRState,
      context: PayrollProcessingContext
  ) -> List[Transaction]: ...
  ```

#### `fire_employee`
- **Reasoning:** Removes dependency on the raw `agent` object. `settlement_system` is now strictly typed, and the transfer relies on the refactored `transfer_from_wallet` method.
- **Before:**
  ```python
  def fire_employee(self, hr_state: HRState, firm_id: int, agent: Any, wallet: IWallet, settlement_system: Any, employee_id: int, severance_pay: float) -> bool: ...
  ```
- **After:**
  ```python
  def fire_employee(self, hr_state: HRState, firm_id: int, wallet: IWallet, settlement_system: ISettlementSystem, employee_id: int, severance_pay: float) -> bool: ...
  ```

### 4.2. FinanceEngine (`simulation/components/engines/finance_engine.py`)

#### `generate_financial_transactions`
- **Reasoning:** Replaces `government` and `shareholder_registry` with the `ITaxAuthority` and `IShareholderRegistryView` protocols, passed via the `FinancialTransactionContext` DTO.
- **Before:**
  ```python
  def generate_financial_transactions(
      self,
      state: FinanceState,
      firm_id: int,
      wallet: IWallet,
      config: FirmConfigDTO,
      government: Any,
      shareholder_registry: IShareholderRegistry,
      current_time: int,
      market_context: MarketContextDTO,
      inventory_value: float
  ) -> List[Transaction]: ...
  ```
- **After:**
  ```python
  def generate_financial_transactions(
      self,
      state: FinanceState,
      context: FinancialTransactionContext
  ) -> List[Transaction]: ...
  ```

#### `invest_in_automation`, `invest_in_rd`, `invest_in_capex`
- **Reasoning:** Consolidates all investment calls into a single pattern using the `InvestmentContext` DTO. This removes the `agent` and `government` objects completely.
- **Before:**
  ```python
  def invest_in_rd(self, state: FinanceState, agent: IFinancialEntity, wallet: IWallet, amount: float, government: Any, settlement_system: Any) -> bool: ...
  ```
- **After:**
  ```python
  def execute_investment(self, state: FinanceState, context: InvestmentContext) -> bool:
      """A single method to handle all forms of investment (R&D, CAPEX, etc.)."""
      ...
  ```

### 4.3. SalesEngine (`simulation/components/engines/sales_engine.py`)

#### `generate_marketing_transaction`
- **Reasoning:** Replaces the full `government` object with a simple `recipient_id`, as the engine only needs to know where to direct the payment.
- **Before:**
  ```python
  def generate_marketing_transaction(self, state: SalesState, firm_id: int, wallet_balance: float, government: Any, current_time: int) -> Optional[Transaction]: ...
  ```
- **After:**
  ```python
  def generate_marketing_transaction(self, state: SalesState, firm_id: int, wallet_balance: float, recipient_id: int, current_time: int) -> Optional[Transaction]: ...
  ```

## 5. Risk & Impact Audit

*   **Cascading Refactor of `SettlementSystem` (HIGH):** This entire plan is contingent on refactoring `SettlementSystem`. The scope of this task is non-trivial and must be completed first. All engine methods making payments (`invest_*`, `fire_employee`) depend on this.
*   **Widespread Test Breakage (HIGH):** Every unit and integration test that instantiates and calls the affected engine methods will fail. A dedicated, large-scale effort will be required to update the entire test suite. This process will likely uncover other hidden dependencies or fragile tests.
*   **God-Class Containment (MEDIUM):** The introduction of DTOs (`PayrollProcessingContext`, etc.) requires the calling code (e.g., `Firm.run_hr_cycle`) to construct these objects. Care must be taken to ensure this construction logic does not add significant complexity back into the `firm.py` file, defeating the purpose of the refactor.
*   **Protocol Implementation Overhead (LOW):** The `Government` class must be updated to implement the `ITaxAuthority` protocol. This is a straightforward task but must be tracked.

## 6. Verification Plan

1.  **Unit Testing (Engines):** Each refactored engine method will be unit tested in **complete isolation**. Dependencies (e.g., `ITaxAuthority`, `IWallet`) will be replaced with dedicated mock objects created using `unittest.mock` that conform to the protocol.
2.  **Unit Testing (Protocols):** A small set of tests will ensure that `Government` and other classes correctly implement their new protocols.
3.  **Integration Testing:** Existing integration tests for agent lifecycles (e.g., `test_firm_lifecycle`) must be updated to use the new engine signatures. These tests will verify that the new DTOs are constructed correctly and the engines are wired properly.
4.  **Golden Data Adherence:** The `golden_households` and `golden_firms` fixtures should still be usable. Test mocks will be configured with data derived from these golden samples to ensure realistic test scenarios. DTO schema changes are not expected, so no "Harvesting" is immediately required.

## 7. Mandatory Reporting Verification

All insights, unforeseen challenges, or technical debt discovered during the implementation of this specification will be logged in a new file under `communications/insights/TDR-001_Engine_Refactor.md`. This report is a mandatory deliverable for the completion of this task.
