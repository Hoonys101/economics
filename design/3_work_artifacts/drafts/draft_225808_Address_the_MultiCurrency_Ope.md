# Spec: Multi-Currency Financial Awareness (TD-032)

## 1. Overview

This document outlines the necessary changes to address **TD-032: Multi-Currency Operational Blindness**. Firm agents currently make critical financial decisions based on an incomplete picture, often considering only their primary currency reserves. This leads to inaccurate valuations, suboptimal capital management, and flawed risk assessments.

The goal is to refactor the firm's financial reporting and decision-making pipeline to be fully currency-aware, utilizing exchange rates provided in the `DecisionContext` to accurately aggregate and assess a firm's complete financial position.

## 2. Phased Implementation Plan

### Phase 1: DTO Contract Refactoring (Breaking Change)

The foundational step is to fix the data contracts to correctly represent a multi-currency reality. All downstream components will be updated to adhere to this new contract.

#### 2.1. `FinanceStateDTO` Update

The `FinanceStateDTO` will be updated to stop representing complex financial data as simple floats.

**Location**: `simulation/dtos/department_dtos.py` (and mirrored in `modules/finance/dtos.py`)

**Changes**:

- **[REPLACE]** `balance: float` -> `wallet: MultiCurrencyWalletDTO`
- **[REPLACE]** `revenue_this_turn: float` -> `revenue_this_turn: Dict[CurrencyCode, float]`
- **[REPLACE]** `expenses_this_tick: float` -> `expenses_this_tick: Dict[CurrencyCode, float]`
- **[ADD]** `total_assets_primary_currency: float`: The firm's total asset value (cash, inventory, capital) converted to its primary currency.
- **[ADD]** `working_capital_primary_currency: float`: The firm's working capital converted to its primary currency.

#### 2.2. `FirmStateDTO.from_firm` Factory Update

The factory method must be enhanced to accept exchange rates to perform the necessary conversions for the new DTO fields.

**Location**: `simulation/dtos/firm_state_dto.py`

**Signature Change**:
```python
# From
@classmethod
def from_firm(cls, firm: Any) -> "FirmStateDTO":

# To
@classmethod
def from_firm(cls, firm: Any, exchange_rates: Dict[CurrencyCode, float]) -> "FirmStateDTO":
```

**Pseudo-code for Implementation**:

```python
# Inside FirmStateDTO.from_firm:

# ... (HR and other DTOs)

# --- Finance State ---
finance = firm.finance
wallet_dto = MultiCurrencyWalletDTO(balances=finance.get_all_balances())

# Perform currency-aware calculations using the provided exchange rates
valuation_dto = finance.calculate_valuation(exchange_rates=exchange_rates)
z_score = finance.calculate_altman_z_score(exchange_rates=exchange_rates)

# Calculate total assets and working capital in primary currency
# These methods in FinanceDepartment must also be updated (see Phase 2)
total_assets = finance.get_total_assets_in_primary_currency(exchange_rates)
working_capital = finance.get_working_capital_in_primary_currency(exchange_rates)


finance_dto = FinanceStateDTO(
    wallet=wallet_dto,
    revenue_this_turn=finance.revenue_this_turn.copy(),
    expenses_this_tick=finance.expenses_this_tick.copy(),
    # ... other fields like profit_history
    altman_z_score=z_score,
    valuation=valuation_dto.amount, # Store as primary currency float
    total_assets_primary_currency=total_assets,
    working_capital_primary_currency=working_capital,
    # ... other fields
)

# ...

return cls(
    # ...
    finance=finance_dto,
    # ...
)
```

### Phase 2: `FinanceDepartment` Internal Logic Update

The `FinanceDepartment` must be updated to perform its internal calculations with full currency awareness.

**Location**: `simulation/components/finance_department.py`

**Methods to Update**:

The following methods must be updated to accept `exchange_rates: Dict[CurrencyCode, float]` and use it to convert all currency holdings to the primary currency before aggregation.

- `calculate_altman_z_score`: Already supports optional `exchange_rates`, make it non-optional or ensure context is always passed.
- `calculate_valuation`: Same as above.
- `get_book_value_per_share`: Must convert all wallet balances to primary currency to calculate net assets correctly.
- `get_inventory_value`: Currently assumes prices are in primary currency. This is acceptable for now but should be noted as a future technical debt item if inventory can be priced differently.

**New Helper Methods**:

- **`get_total_assets_in_primary_currency(self, exchange_rates: Dict) -> float`**:
  - Convert all cash from wallet to primary currency.
  - Add capital stock value.
  - Add inventory value.
  - Return total.
- **`get_working_capital_in_primary_currency(self, exchange_rates: Dict) -> float`**:
  - Get total assets from the method above.
  - Subtract total debt (which is assumed to be in primary currency).
  - Return result.

### Phase 3: `FinancialStrategy` Adaptation

Decision-making logic must be updated to use the new, accurate DTO fields.

**Location**: `simulation/decisions/firm/financial_strategy.py`

**Refactor `_manage_debt`**:
```python
# Inside _manage_debt

# [OLD LOGIC]
# current_assets_raw = firm.finance.balance
# if isinstance(current_assets_raw, dict):
#     current_assets_val = current_assets_raw.get(DEFAULT_CURRENCY, 0.0)
# current_assets = max(current_assets_val, 1.0)

# [NEW LOGIC]
current_assets = max(firm.finance.total_assets_primary_currency, 1.0)

# The rest of the leverage calculation proceeds as before, but now based on a correct total asset value.
```

**Refactor `_attempt_secondary_offering`**:
The trigger for an SEO is low operational cash. This should remain based on the primary currency, as operating costs are typically paid in it.

```python
# Inside _attempt_secondary_offering

# [OLD LOGIC]
# current_balance_raw = firm.finance.balance
# if isinstance(current_balance_raw, dict):
#     current_balance = current_balance_raw.get(DEFAULT_CURRENCY, 0.0)

# [NEW LOGIC]
current_balance = firm.finance.wallet.balances.get(firm.finance.primary_currency, 0.0)

# The rest of the logic proceeds as before, but the trigger is now an explicit, safe access.
```

## 3. Verification Plan

- **Unit Tests**:
  - `FinanceDepartment`: Add tests for new helper methods (`get_total_assets...`). Update tests for `calculate_valuation` and `calculate_altman_z_score` to pass `exchange_rates` and validate correct multi-currency aggregation.
  - `FirmStateDTO`: Update tests for `from_firm` to pass `exchange_rates` and check that the resulting `FinanceStateDTO` is correctly populated.
- **Integration Tests**:
  - Create a test scenario with a firm that has low primary currency but high reserves in another currency.
    - **Verification 1**: The firm should **not** trigger a cash-crunch emergency action like an SEO.
    - **Verification 2**: The firm's leverage calculation in `FinancialStrategy` should be low, reflecting its true total asset value, preventing it from taking on unnecessary debt.
- **Golden Fixtures**:
  - Use `scripts/fixture_harvester.py` to create new golden fixtures of firms with diverse, multi-currency wallets to be used in the updated tests. Refer to `tests/conftest.py` for loading `golden_households` and `golden_firms`.

## 4. Risk & Impact Audit (from Pre-flight Check)

- **Risk 1: God Class & Hidden Dependencies**: `FinanceDepartment` is a "God Class". Changes must surgically inject `exchange_rates` into its methods. Modifying numerous internal call sites is a high risk.
- **Risk 2: DTO Generation Context**: The signature of `FirmStateDTO.from_firm` *must* be changed to accept `exchange_rates`. This change will ripple to every place the DTO is constructed, requiring a careful audit of its usage in the simulation's main loop.
- **Risk 3: Cascading DTO Contract Changes**: Changing `FinanceStateDTO` fields from `float` to currency-aware structures is a major breaking change for all consumers, especially `FinancialStrategy`. Logic like `current_assets_raw.get(DEFAULT_CURRENCY, 0.0)` is proof of existing incorrect usage and must be refactored.
- **Risk 4: Implicit Single-Currency Business Logic**: Critical decision triggers (SEO, loans) are based on single-currency thresholds. Introducing currency conversion will alter firm behavior. The specification must be precise about *how* to aggregate balances for each decision (e.g., total assets for leverage, primary currency only for operational cash).
- **Risk 5: High Risk of Test Failures**: Existing tests are almost certainly dependent on the flawed single-currency behavior. The project must include a dedicated phase for identifying, updating, and validating these tests.

## 5. Mandatory Reporting

Insights and technical debt discovered during this refactoring will be documented in `communications/insights/TD-032-Multi-Currency-Refactor.md`. This includes any compromises made or newly identified areas of single-currency-dependency. This report is a required deliverable for the completion of this task.

---

# API Definition

## `modules/finance/dtos.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from modules.system.api import CurrencyCode
from .dtos import MultiCurrencyWalletDTO # Assumes this DTO exists in a shared location

@dataclass(frozen=True)
class FinanceStateDTO:
    """
    A read-only DTO representing the financial state of an entity, now fully currency-aware.
    """
    # Multi-currency balances
    wallet: MultiCurrencyWalletDTO
    revenue_this_turn: Dict[CurrencyCode, float] = field(default_factory=dict)
    expenses_this_tick: Dict[CurrencyCode, float] = field(default_factory=dict)

    # Key metrics converted to primary currency for decision-making
    total_assets_primary_currency: float
    working_capital_primary_currency: float
    valuation: float # Market valuation in primary currency
    altman_z_score: float

    # Other financial indicators
    profit_history: List[float] = field(default_factory=list) # History of total profit in primary currency
    consecutive_loss_turns: int = 0
    total_shares: float = 0.0
    treasury_shares: float = 0.0
    dividend_rate: float = 0.0
    is_publicly_traded: bool = False
```

## `modules/finance/api.py`
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from modules.system.api import CurrencyCode
from .dtos import MoneyDTO, MultiCurrencyWalletDTO, FinanceStateDTO

# ... (other interfaces like IFinancialEntity)

class IFinanceDepartment(ABC):
    """
    Interface for a firm's Finance Department, outlining its core currency-aware capabilities.
    """

    @property
    @abstractmethod
    def primary_currency(self) -> CurrencyCode:
        ...

    @abstractmethod
    def get_all_balances(self) -> Dict[CurrencyCode, float]:
        ...

    @abstractmethod
    def calculate_valuation(self, exchange_rates: Dict[CurrencyCode, float]) -> MoneyDTO:
        """
        Calculates the firm's total valuation, converted to its primary currency.
        Requires exchange rates for accurate aggregation.
        """
        ...

    @abstractmethod
    def calculate_altman_z_score(self, exchange_rates: Dict[CurrencyCode, float]) -> float:
        """
        Calculates the Altman Z-Score for bankruptcy risk assessment.
        Requires exchange rates for accurate aggregation of financial ratios.
        """
        ...
    
    @abstractmethod
    def get_total_assets_in_primary_currency(self, exchange_rates: Dict[CurrencyCode, float]) -> float:
        """
        Calculates the firm's total assets (cash, capital, inventory) converted to its primary currency.
        """
        ...

    @abstractmethod
    def get_working_capital_in_primary_currency(self, exchange_rates: Dict[CurrencyCode, float]) -> float:
        """
        Calculates the firm's working capital (assets - liabilities) in its primary currency.
        """
        ...

    @abstractmethod
    def get_financial_snapshot_dto(self, exchange_rates: Dict[CurrencyCode, float]) -> FinanceStateDTO:
        """
        Creates a comprehensive, currency-aware DTO of the firm's financial state.
        """
        ...

    # ... other methods like record_revenue, generate_transactions, etc.
```
