modules/market/api.py
```python
"""
Market Domain API Definitions.

This module defines the strict protocols and DTOs required for market interactions,
specifically focusing on housing transactions and property ownership to resolve
behavioral regressions and enforce zero-sum integrity.
"""

from typing import Protocol, List, Dict, Any, Optional, Union, runtime_checkable
from dataclasses import dataclass
from enum import Enum

# Using common types assuming they exist in core; if not, defining simplified versions here
# to ensure self-contained API draft.
TransactionId = str
AgentId = Union[str, int]
Currency = str
ItemId = str

@dataclass
class MarketConfigDTO:
    """Configuration DTO for market mechanics."""
    transaction_fee: float = 0.0
    housing_max_ltv: float = 0.8
    housing_mortgage_term: int = 300

@runtime_checkable
class IPropertyOwner(Protocol):
    """Protocol for agents that can own real estate properties."""
    
    id: AgentId
    owned_properties: List[ItemId]

    def add_property(self, property_id: ItemId) -> None:
        """Transfers ownership of a property to this agent."""
        ...

    def remove_property(self, property_id: ItemId) -> None:
        """Removes ownership of a property from this agent."""
        ...

@runtime_checkable
class IFinancialAgent(Protocol):
    """Protocol for agents that can hold currency and transact."""
    
    id: AgentId
    
    def get_balance(self, currency: Currency) -> float:
        """Returns the current balance of the specified currency."""
        ...

    def deposit(self, amount: float, currency: Currency) -> None:
        """Increases the agent's balance."""
        ...

    def withdraw(self, amount: float, currency: Currency) -> None:
        """Decreases the agent's balance. Should raise error if insufficient funds."""
        ...

@runtime_checkable
class IHousingTransactionParticipant(IPropertyOwner, IFinancialAgent, Protocol):
    """
    Protocol for agents participating in housing market transactions (Buyers).
    Must support both financial operations and property ownership.
    """
    
    current_wage: float
    residing_property_id: Optional[ItemId]
    is_homeless: bool

    # Legacy support check - ideally removed in future refactors
    # _econ_state: Any 

@dataclass
class HousingTransactionContextDTO:
    """
    DTO capturing the system state required to process a housing transaction.
    Decouples the handler from the monolithic 'simulation' object.
    """
    settlement_system: Any  # ISettlementSystem
    bank: Any               # ICentralBank
    government: IPropertyOwner
    real_estate_units: List[Any] # List[RealEstateUnit]
    agents: Dict[AgentId, Any]
    config_module: Any # Should be MarketConfigDTO in strict future
    time: int

class TransactionType(Enum):
    HOUSING = "housing"
    GOODS = "goods"
    LABOR = "labor"

@dataclass
class TransactionResultDTO:
    """Result of a transaction processing attempt."""
    success: bool
    reason: Optional[str] = None
    transaction_id: Optional[TransactionId] = None
    metadata: Optional[Dict[str, Any]] = None

```

design/3_work_artifacts/specs/regression_liquidation_spec.md
```markdown
# Spec: Behavioral Regression Liquidation (Firm & Housing)

## 1. Overview

- **Goal**: Resolve specific logic regressions identified in recent test failures (27 reported).
- **Scope**: 
    1. **Firm Inventory**: Restore slot-based inventory management (`InventorySlot` enum awareness).
    2. **Housing Market**: Fix `HousingTransactionHandler` to strictly adhere to `IHousingTransactionParticipant` protocol and ensure zero-sum settlement flow.
    3. **Scenario Tests**: Ensure standard DTOs are correctly propagated to Agent constructors.
- **Key Constraint**: strict adherence to [SEO_PATTERN](../../1_governance/architecture/standards/SEO_PATTERN.md) and [FINANCIAL_INTEGRITY](../../1_governance/architecture/standards/FINANCIAL_INTEGRITY.md).

## 2. Technical Debt & Risks

- **Protocol Mismatch**: Previous implementations relied on `hasattr` checks which caused silent failures when Agents didn't exactly match expected attributes. New strict Protocol enforcement fixes this.
- **Mock Drift**: Tests were mocking "happy paths" that drifted from actual implementation logic (e.g., Bank transfer mechanics).
- **Implicit State**: `HousingTransactionHandler` previously accessed `simulation.config` directly. We introduce `HousingTransactionContextDTO` to explicitly pass dependencies.

## 3. Detailed Design

### 3.1. Firm Inventory Logic (Fixing `tests/test_firm_inventory_slots.py`)

The `Firm` class must distinguish between `MAIN` (Output) and `INPUT` (Raw Materials) inventory slots.

#### 3.1.1. Logic Specification (Pseudo-code)

```python
# In modules/firm/firm.py (or simulation/firms.py)

def add_item(self, item_id: str, quantity: float, slot: InventorySlot = InventorySlot.MAIN, quality: float = 1.0) -> None:
    # 1. Select Target Registry based on Slot
    target_inventory = self.input_inventory if slot == InventorySlot.INPUT else self.inventory
    
    # 2. Update Quantity (Atomic Add)
    current_qty = target_inventory.get(item_id, 0.0)
    
    # 3. Update Quality (Weighted Average)
    current_quality = self.quality_map.get(slot, {}).get(item_id, 1.0)
    new_quality = ((current_qty * current_quality) + (quantity * quality)) / (current_qty + quantity)
    
    # 4. Commit State
    target_inventory[item_id] = current_qty + quantity
    self._update_quality_map(item_id, new_quality, slot)

def remove_item(self, item_id: str, quantity: float, slot: InventorySlot = InventorySlot.MAIN) -> bool:
    # 1. Select Target
    target_inventory = self.input_inventory if slot == InventorySlot.INPUT else self.inventory
    
    # 2. Check Availability
    if target_inventory.get(item_id, 0.0) < quantity:
        return False
        
    # 3. Deduct
    target_inventory[item_id] -= quantity
    return True
```

### 3.2. Housing Transaction Handler (Fixing `tests/unit/markets/test_housing_transaction_handler.py`)

The handler must orchestrate a complex multi-party transaction ensuring no money is created or destroyed (Zero-Sum).

#### 3.2.1. Transaction Flow (Step-by-Step)

1.  **Validation**:
    *   Verify Buyer implements `IHousingTransactionParticipant`.
    *   Verify Seller implements `IPropertyOwner`.
    *   Calculate LTV (Loan-to-Value) and Down Payment.
    *   Check Buyer Solvency (Assets >= Down Payment).

2.  **Execution (Atomic Phase)**:
    *   **Step A: Down Payment**
        *   Transfer `down_payment` from `Buyer` to `EscrowAgent`.
        *   *On Fail*: Abort.
    *   **Step B: Loan Origination (The "Bank Step")**
        *   Call `Bank.grant_loan(buyer_id, amount)`.
        *   *Note*: `grant_loan` typically creates a Deposit for the Buyer.
        *   **CRITICAL**: Immediately `Bank.withdraw_for_customer(buyer, amount)` to "seize" the loan proceeds for the transaction.
        *   *On Fail*: Reverse Step A (Refund Buyer).
    *   **Step C: Loan Proceeds Transfer**
        *   Transfer `loan_amount` from `Bank` to `EscrowAgent`.
        *   *On Fail*: Reverse Step B (Terminate Loan), Reverse Step A.
    *   **Step D: Final Settlement**
        *   Transfer `total_price` from `EscrowAgent` to `Seller`.
        *   *On Fail*: Reverse Step C (Refund Bank), Reverse Step B, Reverse Step A.

3.  **Asset Transfer**:
    *   `Seller.remove_property(unit_id)`
    *   `Buyer.add_property(unit_id)`
    *   Update `RealEstateUnit` ownership and Lien info (Mortgage).

#### 3.2.2. Error Handling & Compensation

*   **Compensation Logic**: Every step must have a corresponding "Undo" operation.
    *   `Escrow -> Buyer` (Refund Down Payment)
    *   `Escrow -> Bank` (Refund Proceeds)
    *   `Bank.terminate_loan` (Cancel Debt)

### 3.3. Scenario Tests (Configuration Injection)

Ensure `Scenario` classes initialize Agents with strict DTOs (`AgentCoreConfigDTO`, `FirmConfigDTO`) instead of loose kwargs.

## 4. Verification Plan

### 4.1. New Test Cases
*   **Inventory Slot Separation**: Verify adding wood to `INPUT` does not increase `MAIN` wood stock.
*   **Government Seller**: Verify `handler.handle` works when `seller` is the Government agent (no crash on attribute access).
*   **Escrow Reversal**: Verify full rollback if the Seller rejects the final transfer (e.g., account frozen).

### 4.2. Existing Test Impact
*   `tests/unit/markets/test_housing_transaction_handler.py`: Should pass without modification if the Handler implements the Flow defined in 3.2.1.
*   `tests/test_firm_inventory_slots.py`: Should pass if `Firm` implements 3.1.1.

### 4.3. Risk Audit
*   **DTO Schema**: `HousingTransactionContextDTO` is introduced. Existing calls to `handle()` in `MarketSystem` must be updated to construct this DTO.
*   **Circular Imports**: `modules.market.api` imports `Any`. Ensure `modules.simulation` does not import `modules.market` eagerly.

## 5. Mandatory Reporting

*   [x] Insights recorded in `communications/insights/liquidate-regressions.md`.
*   [x] `TECH_DEBT_LEDGER.md` updated with "Housing Handler Config Coupling" (Resolved by DTO).
```