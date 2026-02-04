# Design Spec: Multi-Currency Migration (Corporate & AI)

## 1. Overview

This document outlines the phased migration of the corporate and AI agent layers to a multi-currency financial system. The primary goal is to eliminate the hardcoded `DEFAULT_CURRENCY` dependency and enable robust financial operations using multiple currencies. This migration follows a strict, sequential plan to minimize risk and ensure financial integrity at each step.

**Success Criteria:**
1.  All firm-level financial data is stored and processed as `Dict[CurrencyCode, float]`.
2.  Decision-making logic (production, investment) correctly handles multi-currency wallets.
3.  Macro-economic metrics are correctly aggregated from multiple currencies using a central exchange rate mechanism.
4.  All tests related to corporate finance pass, and new tests validate multi-currency transactions, ensuring zero financial leakage.

---

## 2. Phased Implementation Plan

### Phase 1: Establish Currency Exchange Foundation

**Objective:** Introduce a centralized, configuration-driven system for currency exchange rates (parity). This is a prerequisite for all other steps.

**Task 1.1: Define Exchange Rate API & DTOs**
- Create a new module: `modules/finance/exchange/`.
- Create `modules/finance/exchange/api.py` to define the public contract for currency conversion.
- Create `modules/finance/exchange/dtos.py` for data transfer objects.

**`modules/finance/exchange/dtos.py`**
```python
from typing import Dict, TypedDict

# Defined in modules/system/api.py, shown here for context
# CurrencyCode = NewType("CurrencyCode", str) 

class ParityRatesDTO(TypedDict):
    """
    DTO holding currency parity rates against a base currency.
    Example: {'USD': 1.0, 'KRW': 1300.0, 'GOLD': 2000.0}
    """
    base_currency: CurrencyCode
    rates: Dict[CurrencyCode, float]

```

**`modules/finance/exchange/api.py`**
```python
from typing import Protocol, Dict
from .dtos import ParityRatesDTO
from modules.system.api import CurrencyCode

class ICurrencyExchange(Protocol):
    """Interface for converting amounts between different currencies."""

    def __init__(self, parity_rates: ParityRatesDTO):
        ...

    def convert(
        self, 
        amount: float, 
        from_currency: CurrencyCode, 
        to_currency: CurrencyCode
    ) -> float:
        """
        Converts a given amount from one currency to another.
        
        Raises:
            KeyError: If a currency is not found in the parity rates.
        """
        ...
```

**Task 1.2: Implement Exchange Engine**
- Create `modules/finance/exchange/engine.py`.
- Implement `CurrencyExchangeEngine` which adheres to the `ICurrencyExchange` protocol.
- Logic: `to_amount = amount / rates[from_currency] * rates[to_currency]`

**Task 1.3: Integrate Parity into Simulation Config**
- Modify `config/simulation.yaml` to include a new section for exchange rates.
- The simulation loader must pass this configuration to create the `CurrencyExchangeEngine` at startup, making it available as a singleton.

**`config/simulation.yaml` (Example Addition)**
```yaml
currency_parity:
  base_currency: "USD"
  rates:
    USD: 1.0
    KRW: 1350.5
    RMB: 7.2
    GOLD: 2350.0 # Ounce
```

### Phase 2: Refactor `FinanceDepartment` God Class

**Objective:** Decompose the monolithic `FinanceDepartment` into smaller, single-responsibility components.

**Task 2.1: Define Sub-Component APIs**
- Create new API files for `Accounting`, `Investment`, and `Tax` within `modules/finance/`.
- These components will operate on multi-currency `Wallet` objects (`Dict[CurrencyCode, float]`).

**`modules/finance/wallet.py` (Reference - Assumed to exist)**
```python
# This is a simplified reference to the existing Wallet concept
from typing import Dict
from modules.system.api import CurrencyCode

Wallet = Dict[CurrencyCode, float]
```

**`modules/finance/accounting/api.py`**
```python
from typing import Protocol
from ..wallet import Wallet
# ... other DTOs for BalanceSheet, etc.

class IAccounting(Protocol):
    """Handles the firm's books."""
    
    def get_balance(self, currency: CurrencyCode) -> float:
        ...

    def get_full_wallet(self) -> Wallet:
        ...

    def record_debit(self, amount: float, currency: CurrencyCode, memo: str):
        ...

    def record_credit(self, amount: float, currency: CurrencyCode, memo: str):
        ...
```

**Task 2.2: Refactor `FinanceDepartment` to a Facade**
- Modify `simulation/components/finance_department.py`.
- The class will no longer contain complex logic. It will hold instances of the new sub-components (`IAccounting`, etc.).
- Methods in `FinanceDepartment` will delegate calls to the appropriate sub-component.

**`simulation/components/finance_department.py` (Pseudo-code)**
```python
class FinanceDepartment:
    def __init__(self, firm, accounting_service: IAccounting, ...):
        self.firm = firm
        self.accounting = accounting_service
        # ... other services

    def pay_wages(self, total_wages: float, currency: CurrencyCode):
        # Was: self.assets -= total_wages
        # Now:
        self.accounting.record_debit(total_wages, currency, "Wages")

    def get_assets(self, currency: CurrencyCode) -> float:
        # Was: return self.assets
        # Now:
        return self.accounting.get_balance(currency)
```

### Phase 3: Eradicate `DEFAULT_CURRENCY` in Decision Logic

**Objective:** Update all firm-level decision-making to be fully multi-currency aware.

**Task 3.1: Refactor `production_strategy.py`**
- **Logic to Change**: `calculate_production_cost`, `check_affordability`.
- **Pseudo-code for `check_affordability`**:
  ```python
  # Old logic:
  # cost = ... # a float
  # if self.firm.finance.get_assets() > cost:
  #     ...

  # New logic:
  cost_wallet: Wallet = calculate_multi_currency_cost(...)
  firm_wallet: Wallet = self.firm.finance.accounting.get_full_wallet()

  can_afford = True
  for currency, amount_needed in cost_wallet.items():
      if firm_wallet.get(currency, 0.0) < amount_needed:
          can_afford = False
          break
  
  if can_afford:
      # ... proceed with production
  ```

**Task 3.2: Refactor `financial_strategy.py`**
- **Logic to Change**: Methods managing cash reserves, loans, and investments.
- All logic must now read from and write to the `Accounting` service's `Wallet`.
- Any logic that aggregates total wealth must use the `ICurrencyExchange` service.

**Pseudo-code for `calculate_total_wealth_for_reporting`**:
```python
exchange_service: ICurrencyExchange = get_exchange_service_from_context()
firm_wallet: Wallet = self.firm.finance.accounting.get_full_wallet()
reporting_currency: CurrencyCode = "USD" # Example

total_wealth = 0.0
for currency, amount in firm_wallet.items():
    total_wealth += exchange_service.convert(amount, currency, reporting_currency)

return total_wealth
```

### Phase 4: Update Metrics and Verification

**Objective:** Ensure macro metrics are accurate and the system is verifiable through robust testing.

**Task 4.1: Refactor `economic_tracker.py`**
- **Logic to Change**: All methods that aggregate firm-level financial data (e.g., `calculate_total_corporate_assets`).
- These methods must now iterate through all firms, get their full `Wallet` from the accounting service, and use the `ICurrencyExchange` service to convert amounts to a common reporting currency before summing them.

**Task 4.2: Create Multi-Currency Test Fixtures**
- **Location**: `tests/conftest.py`
- **Action**: Create a new fixture `golden_firms_multi_currency` using `scripts/fixture_harvester.py`.
- This fixture must contain firms with significant balances in at least two non-default currencies (e.g., `KRW`, `GOLD`).

**Task 4.3: Implement New Verification Tests**
- Create a new test file: `tests/integration/systems/test_multi_currency_integrity.py`.
- **Test Case 1: Cross-Currency Transaction**:
  - A firm buys a good priced in `GOLD` using its `KRW` balance.
  - **Assert**:
    - The firm's `KRW` balance decreases by the correct converted amount.
    - The seller's `KRW` balance increases by the same amount.
    - The total amount of each currency in the system remains unchanged (zero-sum).
- **Test Case 2: Multi-Currency Balance Sheet**:
  - Run a simulation for 10 ticks with multi-currency firms.
  - **Assert**: The sum of assets on the balance sheets of all agents (converted to a base currency) equals the total liabilities and equity.

---

## 3. Mocking & Golden Data Strategy

- **Priority**: Use existing `golden_` fixtures (`golden_households`, `golden_firms`) for all tests that do not specifically require multi-currency validation.
- **Custom Data**: For the new tests in Phase 4, use the `scripts/fixture_harvester.py` and its `GoldenLoader` to load specific snapshots where firms have diverse currency holdings.
- **Prohibition**: Do not use `unittest.mock.MagicMock` to create fake `Firm` or `FinanceDepartment` objects. This practice hides type errors and schema mismatches. Use the provided fixtures, which are generated from real simulation data.
- **🚨 Schema Change Notice**: The introduction of `Wallet` and the decomposition of `FinanceDepartment` is a major schema change. After implementing Phase 2, a new "golden" snapshot of the simulation state MUST be harvested. All existing tests will likely need to be updated to use the new `IAccounting` service API instead of direct `firm.assets` access. This is a significant but necessary part of the migration.

---

## 4. Risk & Impact Audit

### 1. Hidden Dependencies & God Classes
- **Status**: ⚠️ Critical Risk
- **Mitigation**: Phase 2 directly addresses this by decomposing `FinanceDepartment` into `Accounting`, `Investment`, and `Tax` services, enforcing the Single Responsibility Principle. The old class becomes a simple facade, reducing its complexity.

### 2. Dueling Financial Systems (Transitional Debt)
- **Status**: ⚠️ Critical Risk
- **Mitigation**: This plan enforces a full commitment to the `Wallet` system. Phase 3 mandates the removal of single-currency extraction patterns (`.get(DEFAULT_CURRENCY, 0.0)`). The introduction of the `ICurrencyExchange` in Phase 1 provides the necessary tool to properly handle multi-currency operations instead of bypassing them.

### 3. Violations of Single Responsibility Principle (SRP)
- **Status**: ⚠️ High Risk
- **Mitigation**: Addressed in Phase 2 for `FinanceDepartment` and Phase 4 for `economic_tracker.py`. By forcing metric calculations to use the clean `ICurrencyExchange` and `IAccounting` APIs, the responsibility of `economic_tracker` is simplified to aggregation rather than complex financial calculation.

### 4. Risks to Existing Tests
- **Status**: ⚠️ High Risk
- **Mitigation**: Phase 4 and the "Schema Change Notice" explicitly acknowledge this risk. The plan includes a dedicated phase for updating tests and creating new, multi-currency-specific fixtures. The migration is not considered complete until all tests are green.

### 5. Potential Circular Imports
- **Status**: 🟡 Medium Risk
- **Mitigation**: The decomposition in Phase 2 reduces the tight coupling between `Firm` and `FinanceDepartment`. By introducing `IAccounting`, `IInvestment`, etc., components will depend on abstractions, not concrete implementations, making them more modular and breaking the tight `self.firm` access patterns. Future work should consider an event bus, but this refactoring is a sufficient first step.
