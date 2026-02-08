# God Class Decomposition Plan: DECOMP-001

## 1. Executive Summary

This document outlines a strategic decomposition plan for the `firms.py`, `settlement_system.py`, and `government.py` modules. The primary objective is to mitigate the risk of "God Class" saturation by refactoring large, monolithic classes into smaller, more cohesive components that adhere to the project's Orchestrator-Engine pattern. This plan addresses the critical technical debt and architectural risks identified in the pre-flight audit, providing a clear path to improve modularity, testability, and maintainability while respecting existing structural constraints.

## 2. Overarching Principles & Risk Mitigation

This plan is guided by pragmatism, acknowledging the deeply embedded architectural patterns.

1.  **Respect the "Parent Pointer" Pattern**: Existing stateful components (`HREngine`, `FinanceEngine`) and their tight coupling with the `Firm` orchestrator will **not** be refactored at this time. This pattern is considered a core constraint.
2.  **Preserve Compatibility Proxies**: The `firm.hr` and `firm.finance` proxies (`simulation/firms.py:L896-963`) are critical for test stability and will be maintained. Their existence will be documented as a necessary form of technical debt.
3.  **Enforce Purity in New Components**: All **newly created** engines and managers (e.g., `LiquidationEngine`, `EstateManager`) **MUST** adhere to the Purity Gate principle. They will operate on DTOs and specific interfaces (`IWallet`, `ISettlementSystem`), not raw agent objects, to prevent the propagation of abstraction leaks.
4.  **Targeted Decomposition**: The focus is on extracting the most disparate and high-growth logic clusters, primarily from `SettlementSystem` and `Firm`, to achieve the highest architectural return on investment.

---

## 3. Target: `simulation/firms.py`

### 3.1. Problem

The `Firm` class (730 lines) is a complex orchestrator burdened with tangential responsibilities, including asset liquidation and high-level corporate finance, which are distinct from its primary production and market decision-making loops.

### 3.2. Proposed Decomposition

We will extract two distinct logic clusters into their own engines.

#### A. New Component: `LiquidationEngine`
- **Responsibility**: Manages the process of agent bankruptcy, including asset write-offs and returning residual value.
- **Location**: `modules/finance/liquidation_engine.py`

#### B. New Component: `CorporateFinanceEngine`
- **Responsibility**: Handles high-level financial strategy, including IPOs, stock valuation, and market capitalization calculations. This separates strategic finance from the operational finance handled by the existing `FinanceEngine`.
- **Location**: `modules/finance/corporate_finance_engine.py`

### 3.3. API Definitions

#### `modules/finance/api/liquidation_api.py`
```python
from __future__ import annotations
from typing import Protocol, Dict, TYPE_CHECKING
from modules.system.api import CurrencyCode
from modules.finance.dtos import MultiCurrencyWalletDTO

if TYPE_CHECKING:
    from modules.finance.api import IFinancialEntity, IWallet, IInventoryHandler, ICapitalHolder
    from modules.memory.api import MemoryV2Interface

class LiquidationResultDTO:
    """Data Transfer Object for the results of an asset liquidation."""
    assets_returned: MultiCurrencyWalletDTO
    value_destroyed: float

class ILiquidationHandler(Protocol):
    """Defines an entity that holds state subject to liquidation."""
    wallet: IWallet
    inventory: IInventoryHandler
    capital: ICapitalHolder
    memory_v2: MemoryV2Interface | None

class ILiquidationEngine(Protocol):
    """Interface for an engine that handles the liquidation of an entity's assets."""

    def liquidate_assets(
        self,
        entity: ILiquidationHandler,
        current_tick: int
    ) -> LiquidationResultDTO:
        """
        Orchestrates the liquidation of an entity's assets.

        Args:
            entity: The stateful entity providing access to its assets.
            current_tick: The current simulation tick for record-keeping.

        Returns:
            A DTO containing the details of the liquidation outcome.
        """
        ...
```

#### `modules/finance/api/corporate_finance_api.py`
```python
from __future__ import annotations
from typing import Protocol, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.finance.api import IShareholderRegistry, IWallet
    from modules.system.api import MarketContextDTO

class IStockMarketLink(Protocol):
    """A narrow interface representing the firm's link to a stock market."""
    def update_shareholder(self, firm_id: int, owner_id: int, quantity: float) -> None:
        ...

class ICorporateFinanceEngine(Protocol):
    """Interface for handling high-level corporate finance strategies."""

    def execute_ipo(
        self,
        firm_id: int,
        wallet: IWallet,
        total_shares: float,
        treasury_shares: float,
        stock_market: IStockMarketLink
    ) -> None:
        """Registers a firm on the stock market."""
        ...

    def calculate_book_value_per_share(
        self,
        wallet_balance: float,
        total_debt: float,
        total_shares: float,
        treasury_shares: float
    ) -> float:
        """Calculates the book value of a single outstanding share."""
        ...

    def calculate_market_cap(
        self,
        stock_price: float,
        total_shares: float,
        treasury_shares: float
    ) -> float:
        """Calculates the market capitalization based on a given stock price."""
        ...
```

---

## 4. Target: `simulation/systems/settlement_system.py`

### 4.1. Problem

The `SettlementSystem` (653 lines) is a latent God Class with three poorly related responsibilities: core atomic transfers, agent death/inheritance, and monetary policy (minting/burning). This violates the Single Responsibility Principle and complicates maintenance.

### 4.2. Proposed Decomposition

`SettlementSystem` will be refactored into three distinct, highly cohesive components.

#### A. Refactored Component: `SettlementSystem`
- **Responsibility**: Reduced to its core function: executing atomic, zero-sum transfers between financial entities. All inheritance and monetary policy logic will be removed.
- **Location**: `simulation/systems/settlement_system.py` (modified)

#### B. New Component: `EstateManager`
- **Responsibility**: Manages the entire lifecycle of a deceased agent's assets, including escrow creation, lien satisfaction (future), and final distribution to heirs or the state (escheatment).
- **Location**: `modules/governance/estate_manager.py`

#### C. New Component: `MonetaryAuthorityGateway`
- **Responsibility**: Provides a dedicated, explicit gateway for creating (minting) and destroying (burning) currency. It acts as the sole interface for the `CentralBank`'s monetary policy powers.
- **Location**: `modules/finance/monetary_authority_gateway.py`

### 4.3. API Definitions

#### `modules/governance/api/estate_api.py`
```python
from __future__ import annotations
from typing import Protocol, List, Tuple, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from modules.finance.api import IPortfolioHandler, IHeirProvider, IFinancialEntity, ITransaction
    from simulation.dtos.settlement_dtos import LegacySettlementAccount

class IEstateManager(Protocol):
    """Manages the settlement of a deceased agent's estate."""

    def open_estate_account(
        self,
        deceased_agent: IPortfolioHandler | IHeirProvider | IFinancialEntity,
        tick: int
    ) -> LegacySettlementAccount:
        """
        Initiates the settlement process by creating an escrow account for the deceased.
        """
        ...

    def execute_estate_distribution(
        self,
        account_id: int,
        distribution_plan: List[Tuple[Any, float, str, str]], # (Recipient, Amount, Memo, TxType)
        tick: int
    ) -> List[ITransaction]:
        """
        Executes the distribution of assets from the escrow account.
        """
        ...

    def close_estate_account(self, account_id: int, tick: int) -> bool:
        """
        Verifies the account is empty and closes it.
        """
        ...
```

#### `modules/finance/api/monetary_authority_api.py`
```python
from __future__ import annotations
from typing import Protocol, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.finance.api import IFinancialEntity, ITransaction
    from modules.system.api import CurrencyCode

class IMonetaryAuthorityGateway(Protocol):
    """
    Provides a gateway to central bank functions for creating and destroying money.
    """
    def mint_and_transfer(
        self,
        destination: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int,
        currency: CurrencyCode = "USD"
    ) -> Optional[ITransaction]:
        """
        Creates new money and transfers it to a destination agent.
        Requires backing by a central monetary authority.
        """
        ...

    def collect_and_burn(
        self,
        source: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int,
        currency: CurrencyCode = "USD"
    ) -> Optional[ITransaction]:
        """
        Withdraws money from a source agent and removes it from circulation.
        Requires backing by a central monetary authority.
        """
        ...

```

---

## 5. Target: `simulation/agents/government.py`

### 5.1. Problem

The `Government` agent (665 lines) mixes orchestration logic with policy implementation details. Per the audit, fiscal policy logic is a prime candidate for extraction to improve cohesion and align with the Orchestrator-Engine pattern.

### 5.2. Proposed Decomposition

#### A. New Component: `FiscalPolicyEngine`
- **Responsibility**: Encapsulates all logic related to taxes, subsidies, and other fiscal policy instruments. It will calculate tax obligations, determine subsidy amounts, and generate the corresponding transactions.
- **Location**: `modules/government/fiscal_policy_engine.py`

### 5.3. API Definitions

#### `modules/government/api/fiscal_api.py`
```python
from __future__ import annotations
from typing import Protocol, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.finance.api import ITransaction, IFinancialEntity
    from modules.system.api import MarketContextDTO

class TaxableEntityDTO:
    """A DTO representing an entity's data relevant for tax calculation."""
    id: int
    entity_type: str # 'Household', 'Firm'
    income: float
    profits: float
    assets: float
    # ... other relevant fields

class IFiscalPolicyEngine(Protocol):
    """
    Interface for an engine that manages the application of fiscal policy.
    """

    def calculate_and_apply_taxes(
        self,
        taxable_entities: List[TaxableEntityDTO],
        government_treasury: IFinancialEntity,
        market_context: MarketContextDTO,
        tick: int
    ) -> List[ITransaction]:
        """
        Calculates taxes for all entities and generates settlement transactions.
        """
        ...

    def distribute_subsidies(
        self,
        eligible_entities: List[IFinancialEntity],
        government_treasury: IFinancialEntity,
        market_context: MarketContextDTO,
        tick: int
    ) -> List[ITransaction]:
        """
        Determines and distributes subsidies or welfare payments.
        """
        ...
```

---

## 6. Mandatory Reporting Verification
In creating this decomposition plan, the following insights and technical debts have been formally acknowledged and will be tracked:
- **TD-DECOMP-001**: The necessity of preserving the "Parent Pointer" pattern in the `Firm` agent due to high refactoring costs.
- **TD-DECOMP-002**: The preservation of backward-compatibility proxies (`firm.hr`, `firm.finance`) as a critical dependency for test stability.
- **INSIGHT-DECOMP-001**: `SettlementSystem`'s responsibilities have been successfully triaged into `Core Transfers`, `Estate Management`, and `Monetary Policy`, providing a clear path to refactoring.

A formal record of these findings will be logged in `communications/insights/DECOMP-001-God-Class-Plan.md` upon approval of this plan.
