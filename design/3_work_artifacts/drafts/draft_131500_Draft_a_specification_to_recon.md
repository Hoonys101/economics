# Spec: Unified Bankruptcy & Liquidation Protocol

## 1. Overview

This specification details a unified bankruptcy protocol to reconcile the conflicting `Firm.liquidate_assets` (write-off) and `InventoryLiquidationHandler` (sell-off) models. A new central authority, the `BankruptcyManager`, will orchestrate the entire process, ensuring the Single Responsibility Principle (SRP) and the Zero-Sum money supply principle are upheld.

The `Firm` will be a passive entity in its own dissolution. The `BankruptcyManager` will attempt to recover value by selling assets to an `IAssetRecoverySystem` (the "Public Manager"). Any assets that cannot be sold will be written off, preventing the artificial creation of money.

## 2. System Architecture & Component Roles

### 2.1. `BankruptcyManager` (New System)
- **Role**: The central and sole authority for handling firm bankruptcies.
- **Responsibilities**:
    1.  Identify and flag firms for bankruptcy.
    2.  Seize control of the firm's assets.
    3.  Orchestrate the liquidation process using specialized handlers.
    4.  Settle debts with creditors.
    5.  Produce a final `BankruptcyReportDTO`.
    6.  De-register the firm from the simulation.

### 2.2. `ILiquidationHandler` (Revised Component)
- **Role**: A strategy component used by the `BankruptcyManager` to liquidate a *specific type* of asset (e.g., inventory, capital stock).
- **Responsibilities**:
    - Value a specific asset class.
    - Attempt to sell it to the `IAssetRecoverySystem`.
    - Report the outcome (cash recovered, assets written off) to the `BankruptcyManager`.

### 2.3. `IAssetRecoverySystem` (Revised System, a.k.a. Public Manager)
- **Role**: The buyer of last resort for liquidated assets.
- **Responsibilities**:
    - Maintain a finite cash balance, funded by the system treasury (e.g., taxes).
    - Evaluate purchase offers from `ILiquidationHandler`s.
    - Execute purchase if funds are sufficient.
    - Absorb purchased assets into a public stockpile.

### 2.4. `Firm` (Revised Agent)
- **Role**: Becomes a passive data container upon bankruptcy.
- **Responsibilities**:
    - The `liquidate_assets` method is **removed**.
    - Its state is read by the `BankruptcyManager` but not self-modified.

## 3. Detailed Liquidation Flow

The process is executed entirely by the `BankruptcyManager`.

**Trigger**: A firm is identified as bankrupt (e.g., by the `AgentLifecycleManager`).

1.  **Seizure & Escrow Creation**:
    - The `BankruptcyManager` is invoked with the bankrupt `Firm` object.
    - It creates a temporary, isolated financial ledger (an "escrow") to manage the liquidation.
    - The firm's liquid cash is immediately transferred to this escrow account.
    - `Firm.is_bankrupt` is set to `True`, freezing all other actions.

2.  **Asset Valuation & Processing**:
    - The manager iterates through registered `ILiquidationHandler`s (e.g., for `inventory`, `capital_stock`, `automation_tech`).
    - For each handler:
        - The handler is passed the `Firm`'s state.
        - The handler values the assets (e.g., inventory value based on last price with a haircut).

3.  **Attempted Sell-Off**:
    - The handler makes a `sell` request to the `IAssetRecoverySystem`.
    - **Scenario A: Sale Succeeds**:
        - The `IAssetRecoverySystem` has enough funds.
        - It transfers the agreed cash amount to the `BankruptcyManager`'s escrow.
        - The physical assets are transferred from the firm's state to the `IAssetRecoverySystem`.
    - **Scenario B: Sale Fails (Insufficient Funds)**:
        - The `IAssetRecoverySystem` rejects the purchase.
        - No cash is transferred. The assets remain with the firm's estate for now.

4.  **Unsold Asset Write-Off**:
    - After all handlers have attempted to sell their respective assets, the `BankruptcyManager` reviews the estate.
    - Any remaining non-cash assets (those that failed to sell) are written off. Their value becomes zero, and they are removed from the simulation. This upholds the `WO-018` principle of preventing money creation.

5.  **Debt Settlement**:
    - The `BankruptcyManager` queries for the firm's liabilities (e.g., outstanding government bailouts).
    - It uses the cash in the escrow account to pay creditors in a predefined order of priority.

6.  **Final Reporting & Cleanup**:
    - A `BankruptcyReportDTO` is generated, detailing:
        - Initial assets (cash and physical).
        - Cash recovered from asset sales.
        - Assets written off.
        - Amount paid to creditors.
        - Final net loss to the system.
    - The `Firm` object is de-registered and removed from the simulation.

## 4. API & DTO Definitions (`modules/finance/bankruptcy/api.py`)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, TypedDict

from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.systems.api import IAssetRecoverySystem

# --- Data Transfer Objects ---

class LiquidationResultDTO(TypedDict):
    """Result from a single asset class liquidation attempt."""
    asset_type: str
    initial_value: float
    cash_recovered: float
    written_off_value: float

class BankruptcyReportDTO(TypedDict):
    """Final report summarizing the entire bankruptcy event."""
    tick: int
    firm_id: int
    initial_cash: float
    total_cash_from_sales: float
    total_written_off_value: float
    total_recovered_cash: float # initial_cash + total_cash_from_sales
    debts_settled: float
    final_net_loss: float
    liquidation_details: List[LiquidationResultDTO]

# --- Interfaces ---

class ILiquidationHandler(ABC):
    """
    Interface for a strategy component that knows how to liquidate
    a specific class of assets.
    """
    @abstractmethod
    def liquidate(
        self,
        firm: Firm,
        asset_recovery_system: IAssetRecoverySystem,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> LiquidationResultDTO:
        """
        Attempts to convert a specific class of firm's assets into cash.

        Args:
            firm: The bankrupt firm object (as a data source).
            asset_recovery_system: The system entity to sell assets to.
            currency: The currency for the transaction.

        Returns:
            A DTO summarizing the outcome of the liquidation attempt.
        """
        pass

class IBankruptcyManager(ABC):
    """
    Central authority for processing firm bankruptcies.
    """
    @abstractmethod
    def process_bankruptcy(
        self,
        firm: Firm,
        current_tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> BankruptcyReportDTO:
        """
        Orchestrates the full bankruptcy and liquidation process for a firm.

        Args:
            firm: The firm to be liquidated.
            current_tick: The current simulation tick.
            currency: The currency for all transactions.

        Returns:
            A final report detailing the outcome of the bankruptcy.
        """
        pass

```

## 5. `IAssetRecoverySystem` API Refinement

The `IAssetRecoverySystem` in `modules/system/api.py` must be extended or confirmed to have the following:

```python
# In modules/system/api.py (or similar)

class IAssetRecoverySystem(IFinancialEntity): # Must be a financial entity to send/receive funds
    """
    The buyer of last resort for assets from liquidated entities.
    """
    @abstractmethod
    def purchase_distressed_assets(
        self,
        assets: Dict[str, float],
        total_price: float,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> bool:
        """
        Purchases a bundle of assets at a given total price.

        Args:
            assets: A dictionary of item_id to quantity.
            total_price: The price the system must pay for the entire bundle.
            currency: The currency of the transaction.

        Returns:
            True if the purchase was successful (funds were sufficient),
            False otherwise.
        """
        pass

    @abstractmethod
    def receive_liquidated_assets(self, assets: Dict[str, float]) -> None:
        """
        Absorbs the purchased assets into the public stockpile.
        (This method likely already exists).
        """
        pass
```

## 6. Verification Plan & Risk Mitigation

-   **Risk: Money Supply Integrity**.
    -   **Mitigation**: The new flow guarantees zero-sum. Cash only moves via explicit transfers between financial entities (`IAssetRecoverySystem` -> `BankruptcyManager` escrow -> Creditors). Unsold assets are destroyed, not converted to cash, preventing money creation.
    -   **Test**: A new integration test will track the total system money supply before and after a bankruptcy. The total amount must remain unchanged.

-   **Risk: SRP Violation in `Firm`**.
    -   **Mitigation**: `Firm.liquidate_assets` is removed. The `BankruptcyManager` is now the sole responsible party.
    -   **Test**: Unit tests for `Firm` will no longer need to mock liquidation. Tests for `BankruptcyManager` will be created, injecting mock firms and handlers.

-   **Risk: Dependency on Funded "Buyer of Last Resort"**.
    -   **Mitigation**: The flow explicitly includes the failure path where the `IAssetRecoverySystem` cannot afford the assets. In this case, the `ILiquidationHandler` returns a result with `cash_recovered: 0.0`, and the `BankruptcyManager` proceeds to the write-off step.
    -   **Test**: Create two test scenarios for `BankruptcyManager`:
        1.  `IAssetRecoverySystem` has sufficient funds; assert that `cash_recovered` > 0.
        2.  `IAssetRecoverySystem` has zero funds; assert that `cash_recovered` == 0 and `written_off_value` > 0.

-   **Risk: High Risk to Existing Tests**.
    -   **Mitigation**: The `BankruptcyReportDTO` provides a clear, verifiable data structure representing the final state. Existing tests that rely on the old liquidation logic must be identified and updated to assert against the values in this new report. A system-wide audit of tests related to zero-sum accounting and firm valuation is required.
    -   **Test**: A "golden" bankruptcy test will be created with a firm of a known state. The resulting `BankruptcyReportDTO` will be validated against pre-calculated expected values.
