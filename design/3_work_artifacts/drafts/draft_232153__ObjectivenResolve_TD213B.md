# Spec: Multi-Currency Migration for Firms (TD-213-B)

## 1. Introduction

- **Objective**: Resolve technical debt `TD-213-B` by migrating the `Firm` agent and its related financial components from a single-currency (`float`) model to a robust, multi-currency architecture.
- **Scope**: This specification covers changes to DTOs, the `FinanceDepartment`, the `Firm` class facade, AI decision-making inputs, and the testing strategy.
- **Guiding Principles**:
    - Adhere to existing Separation of Concerns (SoC) by containing financial logic within `FinanceDepartment`.
    - Leverage the `ICurrencyHolder` protocol as the standard for all currency-holding entities.
    - Ensure data contracts (`DTOs`) are explicit and currency-aware.

## 2. Phase 1: Data Contract (DTO) Refactoring

The foundation of the migration is the introduction of explicit, currency-aware data structures.

### 2.1. New Core DTOs

The following DTOs will be created in a new file: `modules/finance/dtos.py`.

```python
# modules/finance/dtos.py
from typing import TypedDict, Dict, Optional
from modules.system.api import CurrencyCode

class MoneyDTO(TypedDict):
    """Represents a monetary value with its associated currency."""
    amount: float
    currency: CurrencyCode

class MultiCurrencyWalletDTO(TypedDict):
    """Represents a complete portfolio of assets, keyed by currency."""
    balances: Dict[CurrencyCode, float]

class InvestmentOrderDTO(TypedDict):
    """Defines an internal order for investment (e.g., R&D, Capex)."""
    order_type: str # e.g., "INVEST_RD", "INVEST_AUTOMATION"
    investment: MoneyDTO
    target_agent_id: Optional[int] # For M&A, etc.
```

### 2.2. Modification of System-Level DTOs

The following critical system DTOs in `modules/system/api.py` **must** be updated.

```python
# In modules/system/api.py

# ASSUMPTION: MoneyDTO is moved to a central, importable location like `modules/common/dtos.py`
from modules.common.dtos import MoneyDTO

@dataclass(frozen=True)
class MarketSignalDTO:
    # ... existing fields
    best_bid: Optional[MoneyDTO]        # CHANGED from float
    best_ask: Optional[MoneyDTO]        # CHANGED from float
    last_traded_price: Optional[MoneyDTO] # CHANGED from float
    # ... rest of fields
```

### 2.3. Internal Order Model Overhaul

The `Order` model used for internal firm decisions (e.g., `INVEST_RD`) must be updated. The generic `quantity: float` field, when used for monetary values, must be replaced with a structured `MoneyDTO`.

- **Pseudo-code**:
  ```python
  # In simulation/models/Order.py (or equivalent)
  class Order:
      # ...
      # Deprecate direct use of `quantity` for money
      monetary_amount: Optional[MoneyDTO] = None

      # Example factory method
      @staticmethod
      def create_investment(order_type: str, amount: float, currency: CurrencyCode) -> "Order":
          order = Order(order_type="internal", ...)
          order.monetary_amount = MoneyDTO(amount=amount, currency=currency)
          return order
  ```

## 3. Phase 2: `FinanceDepartment` Implementation

All core financial logic will be implemented here. The `FinanceDepartment` will internally manage a `Dict[CurrencyCode, float]` wallet.

### 3.1. Core Responsibilities
- **Multi-Currency Balance Management**: Implement `deposit`, `withdraw`, and `get_balance` methods that operate on specific currencies.
- **Primary Currency**: The `FinanceDepartment` will have a `primary_currency: CurrencyCode` attribute (from config) to resolve ambiguity in single-value calculations (e.g., valuation for M&A).
- **Metric Calculation**:
    - `get_valuation()`: Must return a `MoneyDTO` in the firm's primary currency. It will convert all assets to the primary currency using exchange rates provided by the `MarketSnapshotDTO`.
    - `get_book_value_per_share()`: Will also return a `MoneyDTO` in the primary currency.
- **Transaction Generation**:
    - `generate_marketing_transaction()`: This logic, currently in `Firm`, will move here. It will calculate the budget based on revenues across all currencies, converting them to the primary currency to determine the final spend amount.
    - All other transaction generation methods (`pay_tax`, `pay_dividends`) must be made currency-aware.

## 4. Phase 3: `Firm` & AI Engine Adaptation

### 4.1. `Firm` as a Facade
The `Firm` class will delegate all financial operations to its `FinanceDepartment`. It will not contain any currency logic itself.

- **`get_agent_data()`**: The `assets` field in the returned dictionary will be changed from a `float` to a `MultiCurrencyWalletDTO`.
- **`ICurrencyHolder` Implementation**: The `Firm`'s `get_assets_by_currency()` method will be a direct pass-through to the `FinanceDepartment`.
- **`make_decision()`**: The `Firm` will receive the updated `MarketSnapshotDTO` and pass it to the decision engine. The `Order` objects returned by the engine are expected to follow the new `MoneyDTO` format for all financial decisions.

### 4.2. AI Decision Engine
The AI engine must be updated to:
1.  **Input**: Parse the `MultiCurrencyWalletDTO` for assets and the `MoneyDTO` for market prices.
2.  **Output**: Generate `Order` objects with the correct `MoneyDTO` structure for investment and pricing decisions.

## 5. Phase 4: Diagnostics and Testing

- **Legacy Diagnostics**:
    - The `WorldState.get_total_system_money_for_diagnostics` method will be maintained.
    - A new `ExchangeRateService` will be introduced, which provides conversion rates from the `MarketSnapshotDTO`.
    - `get_total_system_money_for_diagnostics` will use this service to convert all balances to `DEFAULT_CURRENCY` before summing them, ensuring backward compatibility for existing charts and tools.
- **Testing**:
    - **Golden Fixtures**: `golden_firms` and `golden_households` in `conftest.py` must be updated to have multi-currency wallets.
    - **New Test Cases**:
        - A test must verify a firm correctly calculates its marketing budget from revenues in three different currencies.
        - A test must simulate a market where the price is in `EUR` and confirm the AI agent can correctly interpret it and make a trade.
        - A test must validate that `get_total_system_money_for_diagnostics` returns a correct, converted single float value.

## 6. Risk & Impact Audit

- **Risk 1: Data Contract Brittleness**: **Mitigated** by introducing `MoneyDTO` and updating system-level DTOs. This is the core of the fix.
- **Risk 2: Widespread Test Failure**: **Mitigated** by proposing a compatibility layer (`ExchangeRateService` + updated `get_total_system_money_for_diagnostics`) and a clear plan to update tests.
- **Risk 3: Implicit Currency Logic**: **Mitigated** by moving financial logic into `FinanceDepartment` and defining clear rules for multi-currency calculations (e.g., use of a primary currency).
- **Risk 4: Performance Overhead**: The creation of many small `MoneyDTO` objects may introduce performance overhead. This is an **Accepted Risk** for the benefit of architectural correctness. Post-migration profiling may be required.
- **Risk 5: Migration Complexity**: This is a large-scale change. The risk of error is high. **Mitigation**: The phased approach (DTOs -> FinanceDept -> Firm -> AI -> Tests) provides a structured path to completion, allowing for verification at each step.

---
## 7. Mandatory Reporting
- **Insight Capture**: Upon completion of each phase, the implementing agent (Jules) **must** document any unforeseen challenges, architectural discoveries, or newly identified tech debt in `communications/insights/TD-213-B.md`. This includes documenting every file that was touched and required modification.
- **Schema Change Notice**: The changes to `MarketSignalDTO` require an update to all `GoldenLoader` snapshots and fixtures. This "Harvesting" step must be included in the verification plan.

---
# API Definition: `modules/finance/api.py`

```python
from __future__ import annotations
from typing import Protocol, List, Dict, TYPE_CHECKING
from abc import abstractmethod
from .dtos import MoneyDTO, MultiCurrencyWalletDTO, InvestmentOrderDTO
from modules.system.api import CurrencyCode

if TYPE_CHECKING:
    from simulation.agents.government import Government
    from simulation.core_agents import Household

class IFinanceDepartment(Protocol):
    """
    Interface for a Firm's financial operations, designed for a multi-currency environment.
    """

    @property
    @abstractmethod
    def balance(self) -> Dict[CurrencyCode, float]:
        """Provides direct access to the raw balances dict."""
        ...

    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> float:
        """Gets the balance for a specific currency."""
        ...

    @abstractmethod
    def deposit(self, amount: float, currency: CurrencyCode):
        """Deposits a specific amount of a given currency."""
        ...
    
    @abstractmethod
    def withdraw(self, amount: float, currency: CurrencyCode):
        """Withdraws a specific amount of a given currency. Raises InsufficientFundsError if needed."""
        ...

    @abstractmethod
    def get_financial_snapshot(self) -> Dict[str, MoneyDTO | MultiCurrencyWalletDTO]:
        """Returns a comprehensive, currency-aware snapshot of the firm's financials."""
        ...

    @abstractmethod
    def calculate_valuation(self, exchange_rates: Dict[CurrencyCode, float]) -> MoneyDTO:
        """
        Calculates the firm's total valuation, converted to its primary currency.
        Requires current exchange rates.
        """
        ...
    
    @abstractmethod
    def generate_financial_transactions(
        self, 
        government: Government, 
        all_households: List[Household], 
        current_time: int,
        exchange_rates: Dict[CurrencyCode, float]
    ) -> List[Any]: # Returns List[Transaction]
        """
        Generates all standard financial transactions (taxes, dividends, maintenance)
        in a currency-aware manner.
        """
        ...

    @abstractmethod
    def set_dividend_rate(self, new_rate: float) -> None:
        """Sets the dividend rate."""
        ...
    
    @abstractmethod
    def pay_ad_hoc_tax(self, amount: float, currency: CurrencyCode, reason: str, government: Government, current_time: int) -> None:
        """Pays a one-time tax of a specific currency."""
        ...

class InsufficientFundsError(Exception):
    """
    Custom exception to be raised when an operation cannot be completed due to lack of funds.
    """
    def __init__(self, message: str, required: MoneyDTO, available: MoneyDTO):
        self.required = required
        self.available = available
        super().__init__(f"{message} Required: {required['amount']:.2f} {required['currency']}, Available: {available['amount']:.2f} {available['currency']}")

```
