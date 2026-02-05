# Spec: Bank Profit & Asset Liquidation Refactoring (TD-033 & TD-034)

## 1. Overview

This specification details the necessary architectural refactoring to address two critical technical debts:
1.  **TD-033 (Foreign Asset Loss on Liquidation)**: The current `MonetaryTransactionHandler` is not multi-currency aware, causing value loss and breaking M2 integrity when liquidating assets denominated in foreign currencies.
2.  **TD-034 (Bank Profit Absorption)**: The `Bank` class hardcodes profit remittance to the government, preventing flexible distribution strategies like shareholder dividends.

The goal is to decouple responsibilities, introduce multi-currency awareness, and establish modular systems for bank profit distribution and asset transfers, adhering to the findings of the pre-flight audit report.

## 2. Architecture Refactoring

### 2.1. System Decoupling: SRP Enforcement

To break up the existing "God Classes" (`Bank`, `MonetaryTransactionHandler`), we will introduce two new, specialized components and a new handler.

#### 2.1.1. New System: `BankProfitDistributionSystem`
- **Responsibility**: This system will be solely responsible for executing the distribution of bank profits based on a configurable strategy. It decouples the "what" (profit is made) from the "how" (it's distributed).
- **Trigger**: It will be activated by a new transaction type, `bank_profit_declaration`, which the `Bank` will generate instead of directly remitting funds.
- **Configuration**: The distribution strategy (e.g., `remit_to_government`, `pay_dividends`) will be controlled via `simulation.yaml`.

#### 2.1.2. New Handler: `AssetTransferHandler`
- **Responsibility**: This handler will exclusively manage the side-effects of transferring non-fungible or semi-fungible assets (like stocks and real estate) from a seller to a buyer. It centralizes and standardizes asset ownership changes.
- **Decoupling**: This logic will be entirely removed from `MonetaryTransactionHandler`.

### 2.2. Core Logic Modifications

#### 2.2.1. `Bank.run_tick()` Refactoring
- The existing logic for calculating `net_profit` will be preserved.
- **Removed**: The code block that creates a `bank_profit_remittance` transaction directly to the government will be deleted.
- **Added**: A new `Transaction` of type `bank_profit_declaration` will be generated. This transaction's `price` will be the `net_profit`, and its `metadata` will contain a breakdown of profits by currency.

#### 2.2.2. `TransactionProcessor.execute()` Refactoring
- The `TransactionProcessor` will be modified to orchestrate the new flow.
- For transactions that involve an asset transfer (e.g., `asset_liquidation`), the processor will now invoke two handlers in sequence:
    1.  The appropriate monetary/settlement handler (e.g., `MonetaryTransactionHandler` or `SettlementSystem`) to process the payment.
    2.  If the payment is successful, the new `AssetTransferHandler` to execute the change in asset ownership.

#### 2.2.3. `MonetaryTransactionHandler` Simplification
- The `_apply_asset_liquidation_effects` method and all its children (`_handle_stock_side_effect`, `_handle_real_estate_side_effect`) will be **deleted**.
- The handler's responsibility will be reduced to only handling the monetary minting/burning aspects of QE/QT and lender of last resort operations.

### 2.3. Multi-Currency Design (`ICurrencyAware`)

To address TD-033, all financial operations must be currency-aware.
- **DTOs**: Financial DTOs and transaction payloads must represent money as a structure containing `amount` and `currency`. The `Transaction` model's `price` field will be paired with a `currency` field in its `metadata`.
- **`AssetTransferHandler`**: The handler must be able to process a payment in one currency (e.g., `USD`) for an asset denominated in another (e.g., shares of a firm in `EUR`). It will rely on a `ForexMarket` or similar system to get exchange rates when necessary (TBD by implementer).
- **`BankProfitDistributionSystem`**: Must correctly handle profits declared in multiple currencies and distribute them accordingly.

---

## 3. API & DTO Definitions

The following definitions will be placed in `modules/finance/api.py`, `modules/system/api.py`, or a new `modules/assets/api.py` as appropriate.

```python
# In a new `modules/assets/api.py` or similar

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypedDict, Any, TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from simulation.models import Transaction
    from simulation.systems.api import TransactionContext

# DTO for configuration
class ProfitDistributionConfigDTO(TypedDict):
    """
    Defines the strategy for distributing bank profits.
    """
    strategy: str  # e.g., 'remit_to_government', 'pay_dividends'
    dividend_payout_ratio: float # 0.0 to 1.0, portion of profit to pay as dividends

# Interface for a system that can hold and transfer assets
class IAssetOwner(Protocol):
    """
    Represents an agent or entity that can own assets like stocks or real estate.
    This interface unifies access to different portfolio implementations.
    """
    id: Any

    def add_asset(self, asset_id: str, quantity: float, price: float, currency: str) -> None:
        """Adds an asset to the owner's portfolio."""
        ...

    def remove_asset(self, asset_id: str, quantity: float) -> bool:
        """Removes an asset from the owner's portfolio. Returns success."""
        ...

# Interface for the new asset handler
class IAssetTransferHandler(ABC):
    """
    Handles the side-effects of transferring asset ownership between agents.
    """
    @abstractmethod
    def handle_asset_transfer(self, tx: Transaction, buyer: IAssetOwner, seller: IAssetOwner, context: TransactionContext) -> bool:
        """
        Executes the asset transfer based on the transaction details.
        Returns True on success, False on failure.
        """
        pass

# Interface for the new profit distribution system
class IBankProfitDistributionSystem(ABC):
    """
    A system for processing and distributing declared bank profits.
    """
    @abstractmethod
    def execute(self, profit_declaration_tx: Transaction, context: TransactionContext) -> list[Transaction]:
        """
        Takes a 'bank_profit_declaration' transaction and generates
        the resulting fund transfer transactions based on configured strategy.
        """
        pass

```

---

## 4. Logic & Pseudo-code

### 4.1. `Bank.run_tick()`
```python
# ... inside Bank.run_tick() after calculating net_profit_by_currency ...

def run_tick(self, ..., current_tick: int):
    # ...
    net_profit_by_currency = self.calculate_net_profit() # Returns Dict[Currency, float]

    if sum(net_profit_by_currency.values()) > 0:
        # Create a single declaration transaction
        profit_tx = Transaction(
            buyer_id=self.id, # The bank itself
            seller_id=self.government.id, # Symbolic counterparty
            item_id="bank_profit_declaration",
            quantity=1.0,
            price=sum(net_profit_by_currency.values()), # Total profit as primary value
            market_id="internal",
            transaction_type="bank_profit_declaration",
            time=current_tick,
            metadata={
                "currency": "USD", # Base currency for the price field
                "profits_by_currency": net_profit_by_currency
            }
        )
        generated_transactions.append(profit_tx)

    return generated_transactions
```

### 4.2. `BankProfitDistributionSystem.execute()`
```python
def execute(self, profit_tx: Transaction, context: TransactionContext) -> list[Transaction]:
    config: ProfitDistributionConfigDTO = context.config_module.get("bank.profit_distribution")
    profits = profit_tx.metadata['profits_by_currency']
    bank = context.agents.get(profit_tx.buyer_id)
    transactions = []

    if config['strategy'] == 'remit_to_government':
        for currency, amount in profits.items():
            if amount > 0:
                tx = create_transfer_tx(
                    from_agent=bank,
                    to_agent=context.government,
                    amount=amount,
                    currency=currency,
                    memo="bank_profit_remittance"
                )
                transactions.append(tx)

    elif config['strategy'] == 'pay_dividends':
        # 1. Get bank's shareholders from stock market
        shareholders = context.stock_market.get_shareholders(bank.id)
        total_shares = context.stock_market.get_total_shares(bank.id)

        # 2. For each currency, calculate and distribute dividends
        for currency, profit_amount in profits.items():
            if profit_amount <= 0 or total_shares == 0:
                continue

            profit_to_distribute = profit_amount * config['dividend_payout_ratio']
            dividend_per_share = profit_to_distribute / total_shares

            for shareholder_id, shares in shareholders.items():
                payout = dividend_per_share * shares
                shareholder_agent = context.agents.get(shareholder_id)
                if payout > 0 and shareholder_agent:
                    tx = create_transfer_tx(
                        from_agent=bank,
                        to_agent=shareholder_agent,
                        amount=payout,
                        currency=currency,
                        memo="dividend_payment"
                    )
                    transactions.append(tx)

    return transactions
```

### 4.3. `AssetTransferHandler.handle_asset_transfer()`
```python
def handle_asset_transfer(self, tx: Transaction, buyer: IAssetOwner, seller: IAssetOwner, context: TransactionContext) -> bool:
    # 1. Identify asset type from tx.item_id
    asset_id = tx.item_id
    
    # 2. Use the IAssetOwner interface to perform the transfer
    # The protocol ensures we don't need to check agent types (Firm, Household, etc.)
    
    # Attempt to remove from seller first
    if not seller.remove_asset(asset_id, tx.quantity):
        context.logger.error(f"Failed to remove asset {asset_id} from seller {seller.id}")
        return False

    # Add to buyer
    # The currency of the asset price is passed for the buyer's records
    asset_currency = tx.metadata.get("asset_currency", "USD") # Assume a default if not specified
    buyer.add_asset(asset_id, tx.quantity, tx.price, asset_currency)

    # 3. Update market registries (e.g., stock_market)
    if asset_id.startswith("stock_"):
        # ... logic to call context.stock_market.update_shareholder ...
        pass
    elif asset_id.startswith("real_estate_"):
        # ... logic to update unit.owner_id ...
        pass
        
    return True
```

## 5. Verification Plan

-   **TD-033 Test Case**:
    1.  Create an agent holding shares of a firm whose stock is priced in `EUR`.
    2.  Trigger a liquidation of this agent.
    3.  The `asset_liquidation` transaction should have `price` in `USD` (the settlement currency) and `metadata` indicating the asset is `EUR`-denominated.
    4.  **Verify**: The `MonetaryTransactionHandler` correctly mints `USD`.
    5.  **Verify**: The `AssetTransferHandler` correctly transfers the `EUR` stock from the seller to the buyer (e.g., the government).
    6.  **Verify**: The seller's wallet receives the correct amount of `USD`. M2 integrity for both `USD` and `EUR` is maintained system-wide.

-   **TD-034 Test Cases**:
    1.  **Remittance Strategy**: Configure `bank.profit_distribution.strategy` to `remit_to_government`. Run a tick where the bank makes a profit.
        -   **Verify**: The bank generates a `bank_profit_declaration` transaction.
        -   **Verify**: The `BankProfitDistributionSystem` processes this and generates a `bank_profit_remittance` transaction from the bank to the government.
        -   **Verify**: The government's assets increase by the profit amount.
    2.  **Dividend Strategy**: Configure strategy to `pay_dividends` with a `0.5` payout ratio. Ensure the bank has shareholders. Run a tick.
        -   **Verify**: The bank generates a `bank_profit_declaration` transaction.
        -   **Verify**: The `BankProfitDistributionSystem` generates multiple `dividend_payment` transactions to shareholders.
        -   **Verify**: Each shareholder receives a payment proportional to their ownership.
        -   **Verify**: The total payout equals 50% of the bank's profit.

## 6. Risk & Impact Audit

-   **Acknowledged**: This design directly addresses the risks identified in the pre-flight audit: God Classes are broken up, currency awareness is enforced via DTOs and metadata, and entangled logic is decoupled into separate modules. The circular dependency is mitigated by using a transaction-based eventing model (`bank_profit_declaration`).
-   **Impact**:
    -   `simulation/bank.py`: `run_tick` method requires significant modification.
    -   `simulation/systems/transaction_processor.py`: Must be updated to conditionally call the `AssetTransferHandler` after a successful settlement.
    -   `simulation/systems/handlers/monetary_handler.py`: Will be simplified by removing asset transfer logic.
    -   `config/simulation.yaml`: Needs a new section for `bank.profit_distribution`.
-   **New Risk**: The sequence of handlers in `TransactionProcessor` is now critical. The monetary settlement **must** complete successfully before the `AssetTransferHandler` is called. The processor must implement this conditional logic to prevent asset transfers for failed payments.

## 7. Mandatory Reporting Verification

-   Insights and identified technical debt from this design process have been recorded in `communications/insights/TD-033-034_Refactoring.md`. This includes the need for a unified `IAssetOwner` interface and a `ForexMarket` for handling currency conversions during cross-currency liquidations.
