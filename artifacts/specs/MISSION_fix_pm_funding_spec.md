file: modules/system/api.py
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable, TypedDict
from dataclasses import dataclass, field
from enum import IntEnum, auto

# Define Currency Code
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

@dataclass
class MarketContextDTO:
    """
    Context object passed to agents for making decisions.
    Contains strictly external market data (prices, rates, signals).
    """
    market_data: Dict[str, Any]
    market_signals: Dict[str, int]
    tick: int
    exchange_rates: Optional[Dict[str, float]] = None

@dataclass(frozen=True)
class MarketSignalDTO:
    market_id: str
    item_id: str
    best_bid: Optional[int]
    best_ask: Optional[int]
    last_traded_price: Optional[int]
    last_trade_tick: int
    price_history_7d: List[int]
    volatility_7d: float
    order_book_depth_buy: int
    order_book_depth_sell: int
    total_bid_quantity: float
    total_ask_quantity: float
    is_frozen: bool

@dataclass(frozen=True)
class HousingMarketUnitDTO:
    unit_id: str
    price: int
    quality: float
    rent_price: Optional[int] = None

@dataclass(frozen=True)
class HousingMarketSnapshotDTO:
    for_sale_units: List[HousingMarketUnitDTO]
    units_for_rent: List[HousingMarketUnitDTO]
    avg_rent_price: float
    avg_sale_price: float

@dataclass(frozen=True)
class LoanMarketSnapshotDTO:
    interest_rate: float

@dataclass(frozen=True)
class LaborMarketSnapshotDTO:
    avg_wage: float

@dataclass(frozen=True)
class MarketSnapshotDTO:
    """
    A pure-data snapshot of the state of all markets at a point in time.
    """
    tick: int
    market_signals: Dict[str, MarketSignalDTO]
    market_data: Dict[str, Any]
    housing: Optional[HousingMarketSnapshotDTO] = None
    loan: Optional[LoanMarketSnapshotDTO] = None
    labor: Optional[LaborMarketSnapshotDTO] = None

class AgentBankruptcyEventDTO(TypedDict):
    agent_id: int
    tick: int
    inventory: Dict[str, float]
    total_debt: int
    creditor_ids: List[int]

@dataclass(frozen=True)
class PublicManagerReportDTO:
    tick: int
    newly_recovered_assets: Dict[str, float]
    liquidation_revenue: Dict[str, int]
    managed_inventory_count: float
    system_treasury_balance: Dict[str, int]
    cumulative_deficit: int  # Added to track total "bailout" funding injected

@dataclass(frozen=True)
class AssetBuyoutRequestDTO:
    """
    Request payload for the PublicManager to purchase assets from a distressed entity.
    """
    seller_id: AgentID
    inventory: Dict[str, float]
    market_prices: Dict[str, int]  # Current market price (pennies) for valuation
    distress_discount: float = 0.5 # e.g., 50% of market value

@dataclass(frozen=True)
class AssetBuyoutResultDTO:
    """
    Result of an asset buyout operation.
    """
    success: bool
    total_paid_pennies: int
    items_acquired: Dict[str, float]
    buyer_id: AgentID  # PublicManager ID
    transaction_id: Optional[str] = None

class OriginType(IntEnum):
    SYSTEM = 0
    CONFIG = 10
    USER = 50
    GOD_MODE = 100

@runtime_checkable
class ICurrencyHolder(Protocol):
    """
    Protocol for agents/systems that hold currency.
    Used for M2 Money Supply calculation.
    """
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        ...

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        ...

@runtime_checkable
class IAssetRecoverySystem(Protocol):
    """
    Interface for the Public Manager acting as a receiver of assets.
    Now supports active buyout logic to inject liquidity.
    """
    def process_bankruptcy_event(self, event: AgentBankruptcyEventDTO) -> None:
        """
        Legacy ingestion of assets (deprecated in favor of execute_asset_buyout).
        """
        ...

    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        """
        Purchases assets from a distressed agent to provide liquidity for creditor repayment.
        Allowed to go into overdraft (Soft Budget Constraint).
        """
        ...

    def receive_liquidated_assets(self, inventory: Dict[str, float]) -> None:
        """
        Receives inventory from a firm undergoing liquidation (Asset Buyout).
        """
        ...

    def generate_liquidation_orders(self, market_signals: Dict[str, MarketSignalDTO], core_config: Any = None, engine: Any = None) -> List[Any]:
        """
        Generates SELL orders to liquidate managed assets into the market.
        """
        ...

    def get_deficit(self) -> int:
        """
        Returns the cumulative deficit (negative balance) incurred by operations.
        """
        ...

@runtime_checkable
class ISystemFinancialAgent(Protocol):
    """
    Marker interface for system agents (like PublicManager) that are exempt
    from strict solvency checks during specific system operations.
    """
    def is_system_agent(self) -> bool:
        ...
```

file: design/3_work_artifacts/specs/spec_fix_pm_funding.md
```markdown
# Spec: Public Manager Funding & Escheatment Hardening

## 1. Introduction

- **Purpose**: To resolve the "Liquidity Trap" where the Public Manager (PM) cannot acquire assets from bankrupt firms due to a lack of initial funds, causing liquidation failures and asset voids.
- **Scope**: `PublicManager`, `EscheatmentHandler`, and `SettlementSystem` interactions.
- **Goal**: Enable the PM to act as a "Buyer of Last Resort" with a Soft Budget Constraint (Overdraft), ensuring assets are recycled and creditors receive partial repayment.

## 2. Problem Statement

Currently, `PublicManager` implements `IFinancialAgent` with strict solvency checks. When a firm goes bankrupt, its inventory needs to be converted to cash to pay creditors. The PM is the designated buyer, but since `PM.balance = 0`, the purchase transaction fails (`InsufficientFundsError`). Consequently, assets evaporate, and creditors get nothing (Zero Recovery Rate).

## 3. Detailed Design

### 3.1. Public Manager Architecture Update

The `PublicManager` will be upgraded to a `SystemFinancialAgent`.

- **Soft Budget Constraint**: The `_withdraw` method will **NOT** raise `InsufficientFundsError`. Instead, it will allow the balance to go negative.
- **Deficit Tracking**: A new metric `cumulative_deficit` will track how much liquidity the PM has injected into the economy via asset buyouts. This acts as "System Debt".
- **Interface**: Implements `ISystemFinancialAgent` (new marker protocol) to signal special treatment to the Settlement System if needed.

### 3.2. Escheatment & Liquidation Flow (Revised)

The logic in `EscheatmentHandler` (or the Liquidation System calling it) will be split into two distinct phases:

1.  **Phase A: Asset Buyout (Injection)**
    - **Trigger**: Bankrupt Agent has `Inventory > 0`.
    - **Action**: Public Manager executes `execute_asset_buyout`.
    - **Valuation**: Inventory is valued at `Market Price * Distress Discount` (e.g., 50%).
    - **Transfer**: PM transfers `Cash` to Bankrupt Agent (PM balance goes negative).
    - **Outcome**: Bankrupt Agent now has cash. PM holds the inventory.

2.  **Phase B: Debt Settlement (Repayment)**
    - **Trigger**: Bankrupt Agent now has cash from Phase A.
    - **Action**: `LiquidationService` iterates through creditors (Loans, Wages).
    - **Transfer**: Cash flows from Bankrupt Agent to Creditors.

3.  **Phase C: Residual Escheatment (Cleanup)**
    - **Trigger**: Debts paid (or cash exhausted).
    - **Action**: `EscheatmentHandler` transfers *remaining* cash (if any) and any un-bought assets to the Government/PM.
    - **Final State**: Agent Balance = 0, Inventory = 0. Agent removed.

### 3.3. Component Specifications

#### A. `modules/system/execution/public_manager.py`

```python
class PublicManager(IAssetRecoverySystem, ISystemFinancialAgent, IFinancialAgent):
    def __init__(self, ...):
        self.allow_overdraft = True
        self._cumulative_deficit = 0

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        # OVERRIDE: Allow negative balance
        current_bal = self.system_treasury.get(currency, 0)
        self.system_treasury[currency] = current_bal - amount
        if self.system_treasury[currency] < 0:
            self._cumulative_deficit += amount

    def execute_asset_buyout(self, request: AssetBuyoutRequestDTO) -> AssetBuyoutResultDTO:
        total_value = 0
        acquired_items = {}
        
        for item_id, quantity in request.inventory.items():
            price = request.market_prices.get(item_id, 0)
            value = int(price * quantity * request.distress_discount)
            total_value += value
            acquired_items[item_id] = quantity

        # Logic to trigger Settlement Transfer (PM -> Seller)
        # Note: This requires the PM to call SettlementSystem via dependency injection
        # or return an Intent that the Orchestrator executes.
        # For this Spec, we assume the PM calls a rigid 'settle_atomic' or similar wrapper.
        
        self.managed_inventory.update(acquired_items)
        return AssetBuyoutResultDTO(
            success=True,
            total_paid_pennies=total_value,
            items_acquired=acquired_items,
            buyer_id=self.id
        )
```

#### B. `simulation/systems/handlers/escheatment_handler.py`

Refactor to handle the separation of Cash Escheatment (to Gov) vs. Asset Recovery (to PM).

- **Input**: `Transaction` (type=`ESCHEATMENT`)
- **Logic**:
    - If `Transaction.metadata.get('subtype') == 'ASSET_BUYOUT'`:
        - Source: PublicManager
        - Target: Bankrupt Agent
        - Flow: Cash
    - If `Transaction.metadata.get('subtype') == 'RESIDUAL_CASH'`:
        - Source: Bankrupt Agent
        - Target: Government
        - Flow: Cash

## 4. Verification Plan

### 4.1. New Test Cases

1.  **Test PM Overdraft**:
    - Setup: PM Balance = 0.
    - Action: Call `pm.withdraw(1000)`.
    - Assert: PM Balance = -1000. No Exception raised.

2.  **Test Asset Buyout**:
    - Setup: Bankrupt Firm F1 has 10 Widgets (Price=100). PM has 0 Cash.
    - Action: Execute Buyout.
    - Assert:
        - F1 Cash += 500 (50% discount).
        - PM Cash -= 500.
        - PM Inventory += 10 Widgets.
        - F1 Inventory = 0.

3.  **Test Integration (Liquidation Flow)**:
    - Simulate full lifecycle: Bankruptcy -> Buyout -> Creditor Payment -> Residual Escheatment.

### 4.2. Impact Analysis & Risks

- **Risk: Inflation**: Infinite PM spending could devalue currency if assets aren't resold.
    - *Mitigation*: PM has logic to `generate_liquidation_orders` (sell inventory back to market) which burns the recovered cash, reducing the deficit.
- **Risk: Interface Break**: Changing `_withdraw` behavior might confuse other systems expecting strict checks.
    - *Mitigation*: Only PM has this behavior. Other agents remain strict.

## 5. Mandatory Reporting

Insights and Tech Debt resolutions will be logged in `communications/insights/spec-fix-pm-funding.md`.

## 6. Ledger Updates (Tech Debt)

- **Resolves**: `TD-CRIT-PM-MISSING` (Public Manager Ghost/Funding).
- **Resolves**: `TD-CRIT-SYS0-MISSING` (Partial - establishes PM as a system anchor).
```