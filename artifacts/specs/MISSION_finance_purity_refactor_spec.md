File: modules/common/interfaces.py
```python
from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from modules.system.api import CurrencyCode

# Existing protocols
 @runtime_checkable
class IPropertyOwner(Protocol):
    """Protocol for agents that can own real estate properties."""
    owned_properties: List[int]

    def add_property(self, property_id: int) -> None:
        ...

    def remove_property(self, property_id: int) -> None:
        ...

 @runtime_checkable
class IResident(Protocol):
    """Protocol for agents that can reside in a property."""
    residing_property_id: Optional[int]
    is_homeless: bool

 @runtime_checkable
class IMortgageBorrower(Protocol):
    """Protocol for agents that can apply for a mortgage."""
    id: int
    assets: Dict[CurrencyCode, int] # Refined to int (Pennies)
    current_wage: float

 @runtime_checkable
class IInvestor(Protocol):
    """Protocol for agents that hold a portfolio of assets."""
    # Note: 'portfolio' should support .add(symbol, qty, price) and .remove(symbol, qty)
    # Since Portfolio is a complex object, we define the interface it must satisfy or 
    # keep it as Any for now, but strictly typed in implementation.
    portfolio: Any 

# New Protocol for TD-PROTO-MONETARY
 @runtime_checkable
class IIssuer(Protocol):
    """
    Protocol for agents that can issue or repurchase their own equity (Treasury Shares).
    Used to abstract 'Firm' specific logic in transaction handlers.
    """
    id: int
    treasury_shares: float
    total_shares: float

    def repurchase_shares(self, quantity: float) -> None:
        """
        Handles the logic of a firm buying back its own stock.
        Should increase treasury_shares and decrease outstanding shares if applicable.
        """
        ...

    def issue_shares(self, quantity: float) -> None:
        """
        Handles the logic of a firm selling/issuing its own stock.
        Should decrease treasury_shares or increase total_shares.
        """
        ...
```

File: design/3_work_artifacts/specs/MISSION_finance_purity_spec.md
```markdown
# Specification: Finance Protocol Purity (TD-PROTO-MONETARY)

## 1. Overview
This specification addresses **TD-PROTO-MONETARY** by refactoring the `MonetaryTransactionHandler` to remove concrete dependencies on `Firm` and `Household` classes. It introduces the `IIssuer` protocol to handle corporate actions (Buybacks/Issuance) abstractly, ensuring compliance with the **Stateless Engine & Orchestrator (SEO)** pattern and **Protocol Purity** standards.

## 2. Goals
- **Decouple**: Remove imports of `Firm` and `Household` from `simulation/systems/handlers/monetary_handler.py`.
- **Abstract**: Replace `isinstance(obj, Firm)` with `isinstance(obj, IIssuer)` and `isinstance(obj, IInvestor)`.
- **Standardize**: Enforce ` @runtime_checkable` protocols for all financial actors.
- **Maintain**: Preserve existing logic for Stock Buybacks (Firm buying its own stock) vs. Asset Acquisition (Investor buying another's stock).

## 3. Impact Analysis & Risk Assessment (Pre-Implementation Audit)

| Risk Category | Risk Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Logic Regression** | Treating a "Buyback" as a generic "Investment" if ID matching fails. | Strict ordering: Check ID match + `IIssuer` *before* checking `IInvestor`. |
| **Test Failure** | Mocks in `tests/` might not implement `IIssuer` or `IInvestor` protocols correctly. | Update `conftest.py` and test mocks to `spec=RealClass` or explicitly implement protocol methods. |
| **Runtime Crash** | `AttributeError` if a `Protocol` is assumed but not enforced at runtime. | Use `isinstance(obj, Protocol)` guards. Fail gracefully or log warning if protocol missing. |
| **Type Precision** | `IInvestor.portfolio` is `Any`. Runtime behavior might vary. | Ensure all `portfolio` objects expose `.add()` and `.remove()` methods. |

## 4. Architectural Changes

### 4.1. New Protocols (`modules/common/interfaces.py`)
- **`IIssuer`**:
    - `id`: int
    - `treasury_shares`: float
    - `total_shares`: float
    - `repurchase_shares(quantity: float)`: Abstract method for buyback logic.
    - `issue_shares(quantity: float)`: Abstract method for issuance logic.

### 4.2. `MonetaryTransactionHandler` Refactoring (`simulation/systems/handlers/monetary_handler.py`)

#### Current Logic (Anti-Pattern):
```python
if isinstance(seller, Firm) and seller.id == firm_id:
    seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
elif isinstance(seller, IInvestor):
    seller.portfolio.remove(firm_id, tx.quantity)
```

#### New Logic (Protocol-Based):
```python
# 1. Extract Firm ID from Item ID (e.g., "stock_101")
try:
    target_firm_id = int(tx.item_id.split("_")[1])
except (IndexError, ValueError):
    return # Or Log Error

# 2. Seller Side (Source of Stock)
# Priority 1: Is this an Issuance? (Seller is the Issuer)
if isinstance(seller, IIssuer) and seller.id == target_firm_id:
    seller.issue_shares(tx.quantity)
# Priority 2: Is this a Divestment? (Seller is an Investor)
elif isinstance(seller, IInvestor):
    seller.portfolio.remove(target_firm_id, tx.quantity)

# 3. Buyer Side (Destination of Stock)
# Priority 1: Is this a Buyback? (Buyer is the Issuer)
if isinstance(buyer, IIssuer) and buyer.id == target_firm_id:
    buyer.repurchase_shares(tx.quantity)
# Priority 2: Is this an Investment? (Buyer is an Investor)
elif isinstance(buyer, IInvestor):
    price_pennies = int(tx.total_pennies / tx.quantity) if tx.quantity > 0 else 0
    buyer.portfolio.add(target_firm_id, tx.quantity, price_pennies)
```

## 5. Verification Plan

### 5.1. Test Strategy
- **File**: `tests/simulation/systems/test_monetary_handler.py` (Create or Update)
- **Scenarios**:
    1.  **Standard Investment**: `Household` (Investor) buys `stock_101` from `Firm_102` (Investor). -> Verify `portfolio.add`/`remove` called.
    2.  **Stock Buyback**: `Firm_101` (Issuer) buys `stock_101` from `Household`. -> Verify `repurchase_shares` called on Firm, `portfolio.remove` on Household.
    3.  **Stock Issuance**: `Household` buys `stock_101` from `Firm_101` (Issuer). -> Verify `portfolio.add` on Household, `issue_shares` on Firm.
    4.  **Real Estate**: `Household` buys `real_estate_505`. -> Verify `IPropertyOwner` methods.

### 5.2. Mandatory Ledger Audit
Before marking this mission complete, you must:
1.  Run `pytest tests/simulation/systems/handlers/test_monetary_handler.py`.
2.  Update `tests/conftest.py` if global fixtures rely on `Firm` without `IIssuer` methods.
3.  **Critical**: Ensure `Firm` class in `simulation/firms.py` implements `issue_shares` and `repurchase_shares` to satisfy the new `IIssuer` protocol.

## 6. Implementation Steps

1.  **Update Interfaces**: Add `IIssuer` to `modules/common/interfaces.py`.
2.  **Update Firm Model**: Add `issue_shares` and `repurchase_shares` methods to `Firm` class in `simulation/firms/firm.py`.
    - *Note*: Ensure these methods encapsulate the logic currently found in the handler (`treasury_shares` math).
3.  **Refactor Handler**: Rewrite `_handle_stock_side_effect` in `MonetaryTransactionHandler` to use the new logic logic defined in 4.2.
4.  **Run Tests**: Verify strict compliance.
5.  **Report**: Create `communications/insights/finance-purity-spec.md` with findings.
```