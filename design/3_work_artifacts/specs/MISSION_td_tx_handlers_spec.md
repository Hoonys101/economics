File: modules/finance/api.py
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, TypedDict, Union
from dataclasses import dataclass
from enum import Enum

from modules.system.api import AgentID, CurrencyCode, AssetBuyoutRequestDTO, AssetBuyoutResultDTO

# ==============================================================================
# Transaction Types & DTOs
# ==============================================================================

class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    TAX = "TAX"
    BAILOUT = "BAILOUT"
    BOND_ISSUANCE = "BOND_ISSUANCE"
    # Legacy support
    TRADE = "TRADE"

@dataclass(frozen=True)
class BondIssuanceRequestDTO:
    """
    DTO for Bond Issuance Transaction.
    Represents the primary market sale of a bond from an Issuer to a Buyer.
    """
    issuer_id: AgentID
    buyer_id: AgentID
    face_value: int         # Face value per bond in pennies
    issue_price: int        # Actual price paid per bond in pennies
    quantity: int           # Number of bonds
    coupon_rate: float      # Annual coupon rate (0.05 = 5%)
    maturity_tick: int      # Tick when the bond matures
    bond_series_id: Optional[str] = None # Optional ID for grouping

@dataclass(frozen=True)
class TransactionResultDTO:
    """
    Standardized result for any transaction execution.
    """
    success: bool
    transaction_id: str
    timestamp: int
    details: Dict[str, Any]
    error_message: Optional[str] = None

# ==============================================================================
# Interfaces / Protocols
# ==============================================================================

@runtime_checkable
class ITransactionHandler(Protocol):
    """
    Protocol for specialized transaction logic.
    Each TransactionType maps to a concrete implementation of this protocol.
    """
    def validate(self, request: Any, context: Any) -> bool:
        """
        Pure validation logic. Checks solvency, permissions, and data integrity.
        Must NOT mutate state.
        """
        ...

    def execute(self, request: Any, context: Any) -> TransactionResultDTO:
        """
        Executes the transaction.
        Responsible for calling the appropriate System/Service to mutate state.
        """
        ...

    def rollback(self, transaction_id: str, context: Any) -> bool:
        """
        Reverses the transaction effects.
        Critical for Atomic Sagas (TD-INT-BANK-ROLLBACK).
        """
        ...

@runtime_checkable
class IBondMarketSystem(Protocol):
    """
    Interface for the Bond Market System.
    Handles the lifecycle of bond assets (creation, registration, redemption).
    """
    def issue_bond(self, request: BondIssuanceRequestDTO) -> bool:
        """
        Creates the Bond asset, assigns it to the Buyer, and registers the Liability to the Issuer.
        """
        ...
    
    def register_bond_series(self, issuer_id: AgentID, series_id: str, details: Dict[str, Any]) -> None:
        """
        Registers a new bond series in the security master.
        """
        ...

@runtime_checkable
class ITransactionEngine(Protocol):
    """
    Interface for the central Transaction Engine.
    """
    def register_handler(self, tx_type: TransactionType, handler: ITransactionHandler) -> None:
        """
        Registers a handler for a specific transaction type.
        """
        ...

    def process_transaction(self, tx_type: TransactionType, data: Any) -> TransactionResultDTO:
        """
        Dispatches the transaction to the registered handler.
        """
        ...
```

File: design/3_work_artifacts/specs/spec_missing_tx_handlers.md
```markdown
# Spec: Missing Transaction Handlers (Bailout & Bond Issuance)

## 1. Introduction
This specification addresses **TD-RUNTIME-TX-HANDLER** by defining the architectural integration of `BAILOUT` and `BOND_ISSUANCE` transaction types into the `TransactionEngine`. It establishes a registry-based handler pattern to decouple the engine from specific business logic, complying with **Zero-Sum Integrity** and **Protocol Purity**.

## 2. Architectural Design

### 2.1. Registry Pattern
The `TransactionEngine` will transition from a monolithic `if/else` block to a dynamic `HandlerRegistry`.
- **Component**: `TransactionHandlerRegistry`
- **Responsibility**: Map `TransactionType` enum values to `ITransactionHandler` instances.
- **Benefit**: Adheres to Open/Closed Principle. New transaction types can be added without modifying the core engine.

### 2.2. New Handlers

#### A. BailoutHandler
- **Type**: `TransactionType.BAILOUT`
- **DTO**: `AssetBuyoutRequestDTO` (from `modules.system.api`)
- **Logic**:
  1. **Validate**: 
     - Check if `PublicManager` (Buyer) acts as a System Agent (ignoring standard solvency if authorized).
     - Verify Seller owns the assets specified in `inventory`.
  2. **Execute**:
     - Delegate to `IAssetRecoverySystem.execute_asset_buyout`.
     - `IAssetRecoverySystem` handles the asset transfer and cash injection logic internally.
     - Handler records the transaction receipt.
  3. **Rollback**:
     - Inverse operation: PublicManager returns assets, Seller returns cash.

#### B. BondIssuanceHandler
- **Type**: `TransactionType.BOND_ISSUANCE`
- **DTO**: `BondIssuanceRequestDTO` (from `modules.finance.api`)
- **Logic**:
  1. **Validate**:
     - Check if Buyer has sufficient funds (`price * quantity`).
     - Check if Issuer is authorized to issue bonds (e.g., Government or highly rated Firm).
  2. **Execute**:
     - Debit Buyer: `total_cost = issue_price * quantity`.
     - Credit Issuer: `total_cost`.
     - Call `IBondMarketSystem.issue_bond` to create the Bond Asset in Buyer's portfolio and Liability in Issuer's ledger.
  3. **Rollback**:
     - Void the Bond asset.
     - Reverse the cash transfer.

## 3. Data Structures & Interfaces

### 3.1. DTO Updates
- **New**: `BondIssuanceRequestDTO` (See `modules/finance/api.py`)
- **Existing**: `AssetBuyoutRequestDTO` (No changes required, defined in `modules/system/api.py`)

### 3.2. Dependencies
- `IAssetRecoverySystem`: For Bailouts.
- `IBondMarketSystem`: For Bond Lifecycle (New Interface).
- `ISettlementSystem`: For raw cash movement (Atomic Transfers).

## 4. Logical Flow (Pseudo-code)

```python
class TransactionEngine:
    def __init__(self):
        self._handlers: Dict[TransactionType, ITransactionHandler] = {}

    def register_handler(self, tx_type: TransactionType, handler: ITransactionHandler):
        self._handlers[tx_type] = handler

    def submit_transaction(self, tx_type: TransactionType, data: Any) -> TransactionResultDTO:
        handler = self._handlers.get(tx_type)
        if not handler:
            raise ValueError(f"No handler registered for {tx_type}")
        
        # 1. Validation
        if not handler.validate(data, self.context):
            return TransactionResultDTO(success=False, error="Validation Failed")

        # 2. Execution
        try:
            result = handler.execute(data, self.context)
            self._log_transaction(result)
            return result
        except Exception as e:
            # 3. Error Handling
            return TransactionResultDTO(success=False, error=str(e))
```

## 5. Risk & Impact Analysis

- **Risk: Mock Drift (`TD-TEST-TX-MOCK-LAG`)**:
  - **Impact**: Existing tests for `TransactionEngine` might fail if they expect the old monolithic behavior.
  - **Mitigation**: Update `MockTransactionEngine` to support `register_handler` or auto-register default mocks.
- **Risk: Circular Imports**:
  - **Impact**: `BailoutHandler` importing `PublicManager` directly.
  - **Mitigation**: Use `IAssetRecoverySystem` protocol. Ensure `BailoutHandler` is defined in a submodule (e.g., `modules/finance/handlers/bailout.py`) separate from the main engine.
- **Risk: Float Math**:
  - **Impact**: Non-deterministic financial state.
  - **Mitigation**: Strictly enforce `int` types in `BondIssuanceRequestDTO` (pennies).

## 6. Verification Plan

### 6.1. New Test Cases
- `test_bailout_handler_success`: PublicManager buys assets, cash increases for Seller.
- `test_bond_issuance_success`: Buyer pays cash, receives Bond asset. Issuer receives cash.
- `test_bond_issuance_insufficient_funds`: Buyer cannot afford bond -> Failure.
- `test_registry_unknown_type`: Submitting unregistered type throws error.

### 6.2. Existing Test Impact
- `tests/finance/test_transaction_engine.py`: Needs refactoring to use the Registry pattern.
- **Mandatory**: Run full suite. If `test_transaction_engine.py` fails, update the test setup to register dummy handlers.

## 7. Mandatory Reporting
Before implementation, create `communications/insights/spec_missing_tx_handlers.md` and document:
- The decision to use Registry Pattern.
- Verification that `AssetBuyoutRequestDTO` covers all bailout needs.
- Confirmation that existing tests pass after refactoring.
```