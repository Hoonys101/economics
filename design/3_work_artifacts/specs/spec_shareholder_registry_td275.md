# Spec: ShareholderRegistry Service (TD-275)

## 1. Overview

This document specifies the design for a centralized `ShareholderRegistry` service. Its primary purpose is to resolve technical debt `TD-275` by creating a single, efficient source of truth for corporate share ownership.

This service will eliminate the inefficient `O(N*M)` loop currently used in the `FinanceDepartment` for dividend distribution. It achieves this by providing a clean, DTO-based interface that decouples share ownership data from financial transaction logic.

## 2. Interface Specification (`api.py`)

```python
# modules/finance/api.py

from typing import Protocol, List, TypedDict

# --- Data Transfer Objects (DTOs) ---

class ShareholderData(TypedDict):
    agent_id: int
    firm_id: int
    quantity: int

# --- Service Protocol ---

class IShareholderRegistry(Protocol):
    """Single source of truth for stock ownership."""
    def register_shares(self, firm_id: int, agent_id: int, quantity: int) -> None:
        """Adds/removes shares. Zero quantity removes the registry entry."""
        ...
    def get_shareholders_of_firm(self, firm_id: int) -> List[ShareholderData]:
        """Returns list of owners for a firm."""
        ...
    def get_total_shares(self, firm_id: int) -> int:
        """Returns total outstanding shares."""
        ...
```

## 3. Consumer Integration Example (`FinanceDepartment`)

```python
class DividendDistributor:
    def distribute_dividends(self, firm_id: int, total_dividend_payout: float):
        # O(K) lookup instead of O(N*M)
        shareholders = self._registry.get_shareholders_of_firm(firm_id)
        total_shares = self._registry.get_total_shares(firm_id)
        
        if not shareholders or total_shares == 0: return

        dividend_per_share = total_dividend_payout / total_shares
        
        for shareholder in shareholders:
            amount = shareholder['quantity'] * dividend_per_share
            # Use audited Bank/Settlement protocol
            self._bank.submit_payment(firm_id, shareholder['agent_id'], amount)
```

## 4. Verification Plan

1.  **Registry Unit Tests**: Test concurrent share changes and empty states.
2.  **Dividend Optimization Test**: Profile the dividend distribution loop with 2000 agents before and after implementation.
3.  **Persistence Check**: Ensure the registry state is correctly captured in snapshots during serialization.
