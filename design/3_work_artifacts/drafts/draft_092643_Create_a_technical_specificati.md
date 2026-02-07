# Spec: ShareholderRegistry Service (TD-275)

## 1. Overview

This document specifies the design for a centralized `ShareholderRegistry` service. Its primary purpose is to resolve technical debt `TD-275` by creating a single, efficient source of truth for corporate share ownership.

This service will eliminate the inefficient `O(N*M)` loop currently used in the `FinanceDepartment` for dividend distribution. It achieves this by providing a clean, DTO-based interface that decouples share ownership data from financial transaction logic, addressing critical architectural risks like `TD-276` (Raw Agent Coupling) and `TD-274` (God Class Saturation).

- **Associated Technical Debt:** `TD-275`, `TD-276`, `TD-270`, `TD-273`
- **Module:** `modules.finance.registry` (Proposed)

## 2. Interface Specification (`api.py`)

The service will implement the `IShareholderRegistry` protocol, ensuring consumers are decoupled from the concrete implementation.

```python
# Proposed Location: modules/finance/api.py or modules/finance/registry/api.py

from typing import Protocol, List, TypedDict

# --- Data Transfer Objects (DTOs) ---

class ShareholderData(TypedDict):
    """
    Represents the ownership stake of a single agent in a firm.
    This DTO is the sole vehicle for exposing ownership data.
    """
    agent_id: int
    firm_id: int
    quantity: int

# --- Service Protocol ---

class IShareholderRegistry(Protocol):
    """
    Defines the contract for managing and querying stock ownership.

    This service is the single source of truth for which agent owns how many
    shares of which firm. It MUST NOT implement any payment or dividend
    calculation logic.
    """

    def register_shares(self, firm_id: int, agent_id: int, quantity: int) -> None:
        """
        Registers a change in share ownership for a specific agent.
        - A positive quantity increases shares.
        - A negative quantity decreases shares (e.g., selling).
        - If the final quantity is zero or less, the agent is deregistered.

        Args:
            firm_id: The ID of the firm whose shares are being traded.
            agent_id: The ID of the agent owning the shares.
            quantity: The number of shares to add or remove.
        """
        ...

    def get_shareholders_of_firm(self, firm_id: int) -> List[ShareholderData]:
        """
        Retrieves a list of all shareholders for a given firm.

        Returns an empty list if the firm has no shareholders.

        Args:
            firm_id: The ID of the firm to query.

        Returns:
            A list of ShareholderData DTOs representing the firm's owners.
        """
        ...

    def get_total_shares(self, firm_id: int) -> int:
        """
        Calculates the total number of outstanding shares for a firm.

        Args:
            firm_id: The ID of the firm.

        Returns:
            The total count of issued shares.
        """
        ...
```

## 3. High-Level Logic (Pseudo-code)

The implementation will use a nested dictionary to provide efficient lookups.

-   **Internal Data Structure:**
    ```python
    # _share_holdings: dict[int, dict[int, int]]
    # Maps firm_id -> { agent_id -> quantity }
    _share_holdings = {
        101: { 1: 100, 2: 50 },
        102: { 1: 200 }
    }
    ```

-   **`register_shares` Logic:**
    ```python
    def register_shares(self, firm_id, agent_id, quantity_change):
        if firm_id not in self._share_holdings:
            self._share_holdings[firm_id] = {}

        current_shares = self._share_holdings[firm_id].get(agent_id, 0)
        new_shares = current_shares + quantity_change

        if new_shares > 0:
            self._share_holdings[firm_id][agent_id] = new_shares
        else:
            # Remove the shareholder if their holdings drop to or below zero
            self._share_holdings[firm_id].pop(agent_id, None)
    ```

-   **`get_shareholders_of_firm` Logic:**
    ```python
    def get_shareholders_of_firm(self, firm_id):
        if firm_id not in self._share_holdings:
            return []

        shareholders = self._share_holdings[firm_id]
        
        # Convert internal data to a list of DTOs
        return [
            ShareholderData(agent_id=agent_id, firm_id=firm_id, quantity=quantity)
            for agent_id, quantity in shareholders.items()
        ]
    ```

## 4. Consumer Integration Example (`FinanceDepartment`)

This demonstrates the intended use pattern, enforcing separation of concerns.

```python
# In FinanceDepartment (or a dedicated DividendService)

class DividendDistributor:
    def __init__(self, shareholder_registry: IShareholderRegistry, bank_service: IBankService):
        self._registry = shareholder_registry
        self._bank = bank_service # Approved protocol for transactions

    def distribute_dividends(self, firm_id: int, total_dividend_payout: float):
        # 1. Get shareholder data from the registry (O(K) operation)
        shareholders = self._registry.get_shareholders_of_firm(firm_id)
        total_shares = self._registry.get_total_shares(firm_id)

        if not shareholders or total_shares == 0:
            return # No one to pay

        # 2. Calculate dividend per share (Logic lives here, not in registry)
        dividend_per_share = total_dividend_payout / total_shares

        # 3. Create payment instructions
        payments = []
        for shareholder in shareholders:
            payment_amount = shareholder['quantity'] * dividend_per_share
            payments.append(
                PaymentInstruction(
                    source_firm_id=firm_id, 
                    destination_agent_id=shareholder['agent_id'], 
                    amount=payment_amount
                )
            )

        # 4. Execute payments using the existing, audited Bank service protocol
        self._bank.execute_bulk_transfers(payments)

```

## 5. Verification Plan & Mocking Strategy

-   **Golden Data**: Tests will use fixtures from `tests/conftest.py`, specifically `golden_firms` and `golden_households`, to source realistic `firm_id` and `agent_id` values.
-   **Test Cases**:
    1.  **Registration**: Verify `register_shares` correctly adds a new shareholder.
    2.  **Deregistration**: Verify that selling all shares removes an agent from the shareholder list.
    3.  **Update**: Verify that subsequent purchases/sales correctly update an agent's share quantity.
    4.  **Query**: `get_shareholders_of_firm` returns correct `ShareholderData` DTOs.
    5.  **Empty State**: `get_shareholders_of_firm` returns an empty list for a firm with no shares.
    6.  **Total Shares**: `get_total_shares` accurately sums shares from multiple owners.
-   **Mocking**: The `DividendDistributor` consumer will be tested by injecting a mock `IShareholderRegistry` that returns predefined `ShareholderData` lists, isolating the consumer's logic from the registry itself. No `MagicMock` will be used for agent creation.

## 6. Risk & Impact Audit

This design directly mitigates the risks identified in the pre-flight audit.

-   ✅ **`TD-276` (Abstraction Violation)**: The service interface is strictly defined with `agent_id: int`. The implementation will have no knowledge of or access to raw `Household` objects, preventing the critical debt of raw agent coupling.
-   ✅ **`TD-270` & `TD-274` (SRP Violation)**: The service's responsibility is explicitly limited to being a data provider for share ownership. The example in Section 4 proves that dividend calculation and payment logic reside in a separate consumer class, preventing scope creep and protecting the `Bank` class from further saturation.
-   ✅ **`TD-273` (Transactional Integrity)**: The consumer example mandates the use of an existing, approved financial protocol (`IBankService`) for all asset transfers. This prevents consumers from bypassing audited transaction logic.
-   **Dependencies**: The primary consumer, `DividendDistributor`, will have dependencies on `IShareholderRegistry` and `IBankService`. The `ShareholderRegistry` itself has no external service dependencies, making it highly modular and testable.

## 7. Mandatory Reporting Verification

An insight report detailing the architectural benefits of this decoupling has been drafted and will be saved to `communications/insights/TD-275_ShareholderRegistry_Decoupling.md`. This report highlights how the pattern addresses multiple technical debts and serves as a blueprint for future registry-based services.
