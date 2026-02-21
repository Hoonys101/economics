File: modules\finance\api.py
```python
from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union, Callable
from dataclasses import dataclass, field
import abc
from abc import ABC, abstractmethod
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, LoanApplicationDTO, LoanDTO, DepositDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY, CurrencyCode
from modules.simulation.api import AgentID

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.dtos.api import GovernmentSensoryDTO
    from simulation.models import Order, Transaction
    from modules.common.dtos import Claim
    from modules.hr.api import IHRService

# --- Unified DTOs (DTO Hardening) ---

@dataclass(frozen=True)
class DebtStatusDTO:
    """
    Data Transfer Object for Debt Status.
    Strictly uses integers (pennies) for financial precision.
    Replaces legacy float-based structures.
    """
    borrower_id: AgentID
    total_outstanding_debt_pennies: int
    loans: List[LoanDTO]
    is_insolvent: bool
    next_payment_due_pennies: int
    next_payment_due_tick: Optional[int]

# Legacy Compatibility Alias (Deprecated)
LoanInfoDTO = LoanDTO

# --- Core Protocols ---

@runtime_checkable
class IConfig(Protocol):
    """Protocol for configuration module."""
    def get(self, key: str, default: Any = None) -> Any: ...

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Enforces integer-based 'pennies' for all monetary values.
    """
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        ...

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds into the entity's wallet."""
        ...

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws funds from the entity's wallet."""
        ...

@runtime_checkable
class IFinancialAgent(Protocol):
    """
    Protocol for agents participating in the financial system.
    UPDATED: Strictly enforced integer return types for zero-sum integrity.
    """
    id: AgentID

    def get_liquid_assets_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns liquid assets in pennies."""
        ...

    def get_total_debt_pennies(self) -> int:
        """Returns total debt in pennies."""
        ...

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency in pennies."""
        ...

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances in pennies."""
        ...

    @property
    def total_wealth_pennies(self) -> int:
        """Returns the total wealth in default currency estimation (pennies)."""
        ...

    # Legacy float support (Deprecated - should warn or convert)
    def get_liquid_assets(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float: ...
    def get_total_debt(self) -> float: ...

@runtime_checkable
class IFinancialFirm(IFinancialEntity, Protocol):
    """
    Interface for a Firm entity used in financial analysis (e.g., Solvency).
    Ensures strict typing for solvency checks and financial reporting.
    """
    id: AgentID

    @property
    def age(self) -> int: ...

    @age.setter
    def age(self, value: int) -> None: ...

    @property
    def capital_stock_pennies(self) -> int: ...

    @property
    def inventory_value_pennies(self) -> int: ...

    @property
    def monthly_wage_bill_pennies(self) -> int: ...

    @property
    def total_debt_pennies(self) -> int: ...

    @property
    def retained_earnings_pennies(self) -> int: ...

    @property
    def average_profit_pennies(self) -> int: ...

@runtime_checkable
class IFinanceDepartment(Protocol):
    """
    Interface for a Firm's financial operations.
    MIGRATION: All monetary values are integers (pennies).
    """

    @property
    @abstractmethod
    def balance(self) -> Dict[CurrencyCode, int]: ...

    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> int: ...

    @abstractmethod
    def deposit(self, amount: int, currency: CurrencyCode): ...

    @abstractmethod
    def withdraw(self, amount: int, currency: CurrencyCode): ...

    @abstractmethod
    def get_financial_snapshot(self) -> Dict[str, Union[MoneyDTO, MultiCurrencyWalletDTO, float]]: ...

    @abstractmethod
    def calculate_valuation(self, market_context: MarketContextDTO) -> MoneyDTO: ...

    @abstractmethod
    def generate_financial_transactions(
        self,
        government: Any,
        all_households: List[Any],
        current_time: int,
        market_context: MarketContextDTO
    ) -> List[Any]: ...

    @abstractmethod
    def set_dividend_rate(self, new_rate: float) -> None: ...

    @abstractmethod
    def pay_ad_hoc_tax(self, amount: int, currency: CurrencyCode, reason: str, government: Any, current_time: int) -> None: ...

# --- Banking Protocols ---

@runtime_checkable
class IBankService(Protocol):
    """
    Interface for Bank Services used by Markets.
    """
    def get_interest_rate(self) -> float: ...

    def grant_loan(self, borrower_id: int, amount_pennies: int, interest_rate: float, due_tick: int) -> Optional[Tuple[LoanDTO, Any]]: ...

    def stage_loan(self, borrower_id: int, amount_pennies: int, interest_rate: float, due_tick: Optional[int], borrower_profile: Optional[Any]) -> Optional[LoanDTO]: ...

    def repay_loan(self, loan_id: str, amount_pennies: int) -> bool: ...

@runtime_checkable
class IBank(IBankService, IFinancialAgent, Protocol):
    """
    Interface for commercial and central banks.
    """
    base_rate: float

    @abc.abstractmethod
    def get_customer_balance(self, agent_id: AgentID) -> int:
        """Returns customer balance in pennies."""
        ...

    @abc.abstractmethod
    def get_debt_status(self, borrower_id: AgentID) -> DebtStatusDTO:
        """Retrieves the comprehensive debt status for a given borrower."""
        ...

    @abc.abstractmethod
    def terminate_loan(self, loan_id: str) -> Optional["Transaction"]: ...

    @abc.abstractmethod
    def withdraw_for_customer(self, agent_id: AgentID, amount_pennies: int) -> bool: ...

    @abc.abstractmethod
    def get_total_deposits(self) -> int: ...

    @abc.abstractmethod
    def close_account(self, agent_id: AgentID) -> int: ...

    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount_pennies: int) -> int: ...

    @abc.abstractmethod
    def receive_repayment(self, borrower_id: AgentID, amount_pennies: int) -> int: ...

# --- System Protocols ---

@runtime_checkable
class ISettlementSystem(Protocol):
    """
    Interface for the centralized settlement system.
    """
    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount_pennies: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[Any]: ...

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int: ...

@runtime_checkable
class IMonetaryAuthority(ISettlementSystem, Protocol):
    """
    Interface for monetary authority operations.
    """
    def create_and_transfer(
        self,
        source_authority: IFinancialAgent,
        destination: IFinancialAgent,
        amount_pennies: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[Any]: ...

    def transfer_and_destroy(
        self,
        source: IFinancialAgent,
        sink_authority: IFinancialAgent,
        amount_pennies: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[Any]: ...

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        """
        Audits the total M2 money supply in the system.
        M2 = (Cash + Deposits) - Reserves.
        Must handle overdrafts correctly (as debt, not negative cash).
        """
        ...
```

File: design\3_work_artifacts\specs\mod_finance_spec.md
```markdown
# Module A Spec: Finance & DTO Hardening

## 1. Introduction

- **Purpose**: To eliminate float-based non-determinism in financial transactions and rectify the M2 Money Supply calculation logic.
- **Scope**: `modules/finance`, `simulation/systems/accounting.py`, `simulation/systems/settlement_system.py`.
- **Goals**:
    1.  Enforce strict `int` (pennies) for all financial DTOs and Interfaces.
    2.  Fix M2 Inversion bug by treating overdrafts as debt liabilities, not negative cash.
    3.  Implement reciprocal expense logging in Accounting to satisfy Zero-Sum integrity.

## 2. System Architecture

### 2.1. Integer Hardening (TD-CRIT-FLOAT-CORE)
- **Concept**: All monetary values must be `int`. "Float pollution" in core logic is strictly prohibited.
- **Interface Changes**:
    - `IFinancialAgent.get_liquid_assets()` -> `get_liquid_assets_pennies() -> int`
    - `IFinancialAgent.get_total_debt()` -> `get_total_debt_pennies() -> int`
    - `IFinancialAgent.get_balance()` -> returns `int`
- **DTO Unification**:
    - `LoanDTO` (modules/finance/dtos.py) becomes the SSoT.
    - `LoanInfoDTO` (modules/finance/api.py) is deprecated/aliased to `LoanDTO`.
    - `DebtStatusDTO` fields updated to `int`.

### 2.2. M2 Money Supply Logic (TD-ECON-M2-INV)
- **Problem**: Current logic `Total Cash = Sum(Agent Balances)` fails when agents have negative balances (overdrafts), reducing the apparent money supply.
- **New Logic**:
    ```python
    def calculate_m2(agents, bank_reserves):
        # 1. Currency in Circulation (Physical Cash held by non-banks)
        # Floor negative balances at 0. Overdraft is NOT negative cash.
        total_cash_circulation = sum(max(0, a.balance_pennies) for a in agents) - bank_reserves
        
        # 2. Demand Deposits
        total_deposits = bank.get_total_deposits()
        
        # 3. M2
        return total_cash_circulation + total_deposits
    ```
- **Credit Tracking**:
    - Overdrafts are tracked separately as `Total System Credit` (Unsecured Debt).

### 2.3. Reciprocal Accounting (TD-SYS-ACCOUNTING-GAP)
- **Logic**: Every `Transaction` must trigger dual entries in the `AccountingSystem`.
    - **Seller**: `record_revenue(amount)` (Existing)
    - **Buyer**: `record_expense(amount)` (New)
- **Pseudo-Code (accounting.py)**:
    ```python
    def handle_transaction(tx):
        seller.record_revenue(tx.amount_pennies)
        if tx.type == 'GOODS':
            buyer.record_expense(tx.amount_pennies) # Was 'pass'
    ```

## 3. Detailed Design

### 3.1. Class: `IFinancialAgent` (Protocol)
- **Description**: The base contract for all economic agents.
- **API Updates**:
    - `get_liquid_assets_pennies() -> int`: Returns cash + equivalents.
    - `get_total_debt_pennies() -> int`: Returns sum of all loan principals.
    - `total_wealth_pennies -> int`: Property for Net Worth (Assets - Liabilities).

### 3.2. Class: `SettlementSystem`
- **Responsibility**: Execute transfers and calculate system-wide monetary aggregates.
- **New Method**: `audit_total_m2()` implements the "Floored Cash" logic.

## 4. Verification Plan

### 4.1. New Test Cases
- **`test_m2_with_overdrafts`**:
    - Scenario: Agent A has 100, Agent B has -50 (Overdraft).
    - Expectation: M2 = 100 (Cash) + 0 (Deposits) = 100. (Not 50).
    - Verification: `monetary_authority.audit_total_m2()` returns correct value.
- **`test_financial_agent_int_compliance`**:
    - Scenario: Instantiate Household, Firm, Government.
    - Verification: `isinstance(agent.get_liquid_assets_pennies(), int)` is True.
- **`test_accounting_reciprocity`**:
    - Scenario: Firm buys Wood from Market.
    - Expectation: Firm `expenses` increase by `price * quantity`.
    - Verification: Check `AccountingSystem` logs or `Firm` internal tracker.

### 4.2. Existing Test Impact
- **`tests/finance/test_bank.py`**: High impact. Mocks returning floats will break. Must update `MockFinancialAgent` to satisfy new Protocol.
- **`tests/simulation/test_settlement.py`**: Update assertions to expect `int`.

### 4.3. Risk Audit (TD-Review)
- **Critical Risk**: `SolvencyEngine` relies on `get_liquid_assets`. If this returns `int` but the engine expects `float` for division, Python handles it (true division `/`). However, if it expects `float` for type checking, it will fail.
- **Mitigation**: Update `SolvencyEngine` to accept `Union[int, float]` or strictly `int`.
- **Dependency**: `IFinancialAgent` is used by `TaxSystem`. Ensure `calculate_tax` handles `int` inputs correctly.

## 5. Mandatory Reporting
- **Action**: Create `communications/insights/mod-finance-spec.md`.
- **Content**: Document the "Float to Int" migration strategy and the specific M2 formula change.
```