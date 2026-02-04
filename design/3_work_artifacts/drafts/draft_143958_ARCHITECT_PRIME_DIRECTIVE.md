# Spec: Government Module Decomposition (TD-226, TD-227, TD-228)

- **Version**: 2.0
- **Author**: Scribe (Administrative Assistant)
- **Related Tickets**: TD-226 (God Class), TD-227 (Circular Deps), TD-228 (SRP Violation)

## 1. Overview & Goals

This specification outlines the mandatory refactoring of the `Government` agent. The current implementation is a monolithic God Class, leading to tight coupling, circular dependencies, and violations of the Single Responsibility Principle (SRP). These issues present a significant risk to future development, particularly the integration of the `CentralBank` module.

**The primary goals are:**
1.  **Decompose the `Government` God Class** into a set of independent, single-responsibility services.
2.  **Eliminate Circular Dependencies** by removing the practice of passing the `Government` instance (`self`) into component constructors.
3.  **Transform `Government` into a Facade**: Its sole responsibility will be to coordinate the new, independent services.
4.  **Establish Clear Service Boundaries** with `api.py` interfaces to enable robust, independent testing and prepare for `CentralBank` integration.

## 2. Architectural Solution: Facade and Services

The `Government` agent will be refactored to follow the **Facade** design pattern. The core logic will be extracted into the following independent services, each with a clearly defined API.

```
+--------------------------+
|   Government (Facade)    |
| (Coordinator)            |
+------------+-------------+
             |
             v
+--------------------------------------------------------------------+
|                      Service Registry (DI)                         |
+------+---------------+----------------+----------------+-----------+
       |               |                |                |
       v               v                v                v
+------------+  +-------------+  +-------------+  +-------------+
| ITaxService|  |IWelfareService|  |IFiscalService| |IPolicyService|
+------------+  +-------------+  +-------------+  +-------------+
```

- **`Government` (Facade)**: The orchestrator. It holds instances of the services and delegates calls to them. It does **not** contain any business logic itself.
- **`Services` (Components)**: Each service manages a specific domain (e.g., `TaxService`, `WelfareService`). They are initialized independently and receive their dependencies (like `IWallet` or `ISettlementSystem`) via their constructors, not the `Government` instance.

---

## 3. Phase 1: Service Interface & DTO Definition (`api.py`)

The first step is to define the contracts for our new services. This enforces clear boundaries and allows for parallel development and testing.

### 3.1. `modules/government/tax/api.py` (New)

This API defines the contract for all taxation-related logic.

```python
# modules/government/tax/api.py
from typing import Protocol, Dict, Any
from modules.finance.api import TaxCollectionResult
from modules.government.dtos import FiscalPolicyDTO
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class ITaxService(Protocol):
    """
    Interface for the taxation service.
    """

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax amount for a given income and fiscal policy."""
        ...

    def calculate_corporate_tax(self, profit: float, rate: float) -> float:
        """Calculates corporate tax based on profit and a flat rate."""
        ...

    def record_revenue(self, result: TaxCollectionResult) -> None:
        """
        Updates internal ledgers based on a verified tax collection result.
        This method should be the single source of truth for tax revenue logging.
        """
        ...
        
    def get_revenue_this_tick(self) -> Dict[CurrencyCode, float]:
        """Returns the total revenue collected in the current tick."""
        ...

    def get_revenue_breakdown_this_tick(self) -> Dict[str, float]:
        """Returns the breakdown of revenue by tax type for the current tick."""
        ...
        
    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""
        ...

```

### 3.2. `modules/government/welfare/api.py` (New)

This API defines the contract for welfare and social support programs.

```python
# modules/government/welfare/api.py
from typing import Protocol, List, Dict, Any
from simulation.models import Transaction

class IWelfareService(Protocol):
    """
    Interface for the welfare service.
    Handles social safety nets and support for households.
    """
    
    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """Calculates current survival cost based on market prices."""
        ...

    def run_welfare_check(self, households: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Identifies households in need and provides basic support.
        Returns a list of payment transactions.
        """
        ...
        
    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """
        Provides a direct subsidy to a specific household.
        Returns a list of payment transactions.
        """
        ...
        
    def get_spending_this_tick(self) -> float:
        """Returns total welfare spending for the current tick."""
        ...
        
    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulator."""
        ...
```

### 3.3. `modules/government/fiscal/api.py` (New)

This API defines the contract for active fiscal interventions, such as bailouts and infrastructure projects. This decouples firm support from household welfare.

```python
# modules/government/fiscal/api.py
from typing import Protocol, List, Tuple, Optional, Any
from simulation.models import Transaction
from modules.finance.api import BailoutLoanDTO

class IFiscalService(Protocol):
    """
    Interface for fiscal policy actions like bailouts and infrastructure investment.
    """

    def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> Tuple[Optional[BailoutLoanDTO], List[Transaction]]:
        """
        Evaluates and provides a bailout loan to a firm.
        Returns the loan details and settlement transactions.
        """
        ...

    def invest_infrastructure(self, current_tick: int, households: List[Any]) -> List[Transaction]:
        """
        Executes infrastructure investment, potentially boosting productivity.
        Returns a list of payment transactions.
        """
        ...

    def get_stimulus_spending_this_tick(self) -> float:
        """Returns total stimulus spending for the current tick."""
        ...

    def get_infrastructure_level(self) -> int:
        """Returns the current national infrastructure level."""
        ...
        
    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulators."""
        ...
```

---

## 4. Phase 2: Implementation & Logic Migration Plan

Jules will create new service classes that implement the interfaces above and move the corresponding logic from `government.py` into them.

### 4.1. `TaxService` Implementation

-   **Create**: `modules/government/tax/service.py`
-   **Class**: `TaxService(ITaxService)`
-   **Dependencies (Constructor)**: `config_module: Any`.
-   **Logic to Move from `government.py`**:
    -   `calculate_income_tax()` -> `TaxService.calculate_tax_liability()`
    -   `calculate_corporate_tax()` -> `TaxService.calculate_corporate_tax()`
    -   `record_revenue()` -> `TaxService.record_revenue()`
    -   The `TaxationSystem` instance will now be owned by the `TaxService`.
    -   The various tax revenue state variables (`total_collected_tax`, `revenue_this_tick`, etc.) will be moved into `TaxService`.

### 4.2. `WelfareService` Implementation

-   **Create**: `modules/government/welfare/service.py`
-   **Class**: `WelfareService(IWelfareService)`
-   **Dependencies (Constructor)**: `gov_wallet: IWallet`, `settlement_system: ISettlementSystem`, `config_module: Any`.
-   **Logic to Move from `government.py`**:
    -   `get_survival_cost()` -> `WelfareService.get_survival_cost()`
    -   `run_welfare_check()` -> `WelfareService.run_welfare_check()`
    -   `provide_household_support()` -> `WelfareService.provide_household_support()`
    -   The `welfare_spending` state variables will be moved into `WelfareService`.
    -   **Crucially**, `WelfareService` now depends on the `IWallet` interface, not the entire `Government` agent, breaking the circular dependency.

### 4.3. `FiscalService` Implementation

-   **Create**: `modules/government/fiscal/service.py`
-   **Class**: `FiscalService(IFiscalService)`
-   **Dependencies (Constructor)**: `gov_wallet: IWallet`, `finance_system: Any`, `config_module: Any`.
-   **Logic to Move from `government.py`**:
    -   `provide_firm_bailout()` -> `FiscalService.provide_firm_bailout()`
    -   `invest_infrastructure()` -> `FiscalService.invest_infrastructure()`
    -   The `InfrastructureManager` will be instantiated and owned by the `FiscalService`.
    -   State variables `stimulus_spending` and `infrastructure_level` will be moved here.

---

## 5. Phase 3: Refactoring `Government` to a Facade

After implementing the services, the `Government` class will be stripped of its logic and refactored into a lean coordinator.

```python
# simulation/agents/government.py (Refactored Structure)

# Import service interfaces
from modules.government.tax.api import ITaxService
from modules.government.welfare.api import IWelfareService
from modules.government.fiscal.api import IFiscalService
# ... other imports

# Import service implementations
from modules.government.tax.service import TaxService
from modules.government.welfare.service import WelfareService
from modules.government.fiscal.service import FiscalService


class Government(ICurrencyHolder):
    """
    A FACADE for coordinating government-related services.
    It owns the government's state (wallet, portfolio) and delegates
    all business logic to specialized services.
    """
    def __init__(self, id: int, initial_assets: float, config_module: Any, strategy: ...):
        # 1. Owns core state
        self.id = id
        self.wallet = Wallet(self.id, ...)
        self.portfolio = Portfolio(self.id)
        
        # Dependencies for services
        self.settlement_system: Optional["ISettlementSystem"] = None
        self.finance_system: Optional["IFinanceSystem"] = None

        # 2. Instantiate and hold services
        # This can later be replaced by a formal DI container
        self.tax_service: ITaxService = TaxService(config_module)
        self.welfare_service: IWelfareService = WelfareService(self.wallet, self.settlement_system, config_module)
        self.fiscal_service: IFiscalService = FiscalService(self.wallet, self.finance_system, config_module)
        # self.policy_service: IPolicyService = ...

        # ... other non-logic state (political state, etc.)

    # 3. Delegate methods to services
    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        # The fiscal_policy DTO is still determined at the Government level for now
        return self.tax_service.calculate_tax_liability(self.fiscal_policy, income)

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        return self.welfare_service.run_welfare_check(agents, market_data, current_tick)
        
    def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> ...:
        return self.fiscal_service.provide_firm_bailout(firm, amount, current_tick)

    def record_revenue(self, result: TaxCollectionResult):
        self.tax_service.record_revenue(result)
        
    def reset_tick_flow(self):
        """Orchestrates resetting all services for the new tick."""
        self.tax_service.reset_tick_flow()
        self.welfare_service.reset_tick_flow()
        self.fiscal_service.reset_tick_flow()
        # ...

    def finalize_tick(self, current_tick: int):
        # The facade gathers data from services for history/reporting
        welfare_spending = self.welfare_service.get_spending_this_tick()
        stimulus_spending = self.fiscal_service.get_stimulus_spending_this_tick()
        # ... build snapshots and append to history
```

---

## 6. Risk & Impact Audit Resolution

-   **[TD-227: SOLVED] Circular Dependencies**: By removing `WelfareManager(self)` and `InfrastructureManager(self)` and instead providing specific interfaces like `IWallet` to service constructors, the tight coupling and circular dependency risk is eliminated.
-   **[TD-226: SOLVED] God Class**: `Government` is refactored into a Facade. All core business logic is moved to `TaxService`, `WelfareService`, and `FiscalService`.
-   **[TD-228: SOLVED] SRP Violation**: The responsibilities of tax collection (`TaxService`), household support (`WelfareService`), and firm support (`FiscalService`) are now handled by separate, dedicated classes.
-   **`AdaptiveGovBrain` Integrity**: The refactoring ensures the brain remains stateless. The `Government` facade will be responsible for aggregating the `GovernmentStateDTO` from the various services before passing it to the brain, preserving the clean interface.

## 7. Test Migration Strategy

-   **Target Interfaces, Not Implementation**: All existing tests for `government.py` must be refactored.
-   **Create New Test Files**: Create `tests/modules/government/tax/test_tax_service.py`, `tests/modules/government/welfare/test_welfare_service.py`, etc.
-   **Mock Dependencies**: When testing a service (e.g., `WelfareService`), its dependencies (`IWallet`, `ISettlementSystem`) must be mocked. Use `pytest-mock` to provide mock objects that adhere to the API contracts.
-   **Facade Integration Tests**: A smaller set of integration tests for the `Government` facade should verify that it correctly coordinates the (mocked) services.
