I will now generate the markdown document with the proposed fixes.

# Draft Fix: Signature Audit for `IFinancialEntity` (LEAK-002)

## 1. Executive Summary

A system-wide audit of the `IFinancialEntity` protocol and its implementations has revealed critical signature inconsistencies, particularly regarding multi-currency transactions. The `deposit` and `withdraw` methods on the core interface lack a `currency` parameter, leading to implementations that either drop this information or do not support multi-currency balances at all.

This proposal introduces the necessary changes to standardize financial interactions, ensuring that the currency type is preserved across all financial entities. This is a critical step to prevent silent money leaks or corruption when multiple currencies are active in the simulation.

## 2. Problem Analysis

The core issue stems from the `IFinancialEntity` protocol in `modules/finance/api.py`, where `deposit` and `withdraw` methods are defined with only an `amount`. This has led to several problems in concrete implementations:

1.  **Proxy Information Loss**: `GovernmentFiscalProxy` implements the simple interface and calls the multi-currency-aware `Government` agent, but it loses the `currency` information, forcing all proxied transactions to fall back to the default currency.
2.  **Incomplete Implementations**: `EscrowAgent` implements the protocol but only supports a single float balance, making it incompatible with a multi-currency environment.
3.  **Interface/Implementation Mismatch**: The `assets` property of the interface is implicitly typed as `float`, while compliant implementations like `BaseAgent`, `Government`, and `PublicManager` correctly return a `Dict[CurrencyCode, float]`.

## 3. Proposed Changes

### 3.1. `modules/finance/api.py`

The `IFinancialEntity` protocol will be updated to be fully currency-aware.

**Current Implementation:**
```python
# modules/finance/api.py

class IFinancialEntity(Protocol):
    """Protocol for any entity that can hold and transfer funds."""

    @property
    def id(self) -> int: ...

    @property
    def wallet(self) -> IWallet: ...

    @property
    def assets(self) -> float: ...

    def deposit(self, amount: float) -> None:
        """Deposits a given amount into the entity's account."""
        ...

    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount from the entity's account.
        ...
        """
        ...
```

**Proposed New Implementation:**
```python
# modules/finance/api.py

from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class IFinancialEntity(Protocol):
    """Protocol for any entity that can hold and transfer funds."""

    @property
    def id(self) -> int: ...

    @property
    def wallet(self) -> IWallet: ...

    @property
    def assets(self) -> Dict[CurrencyCode, float]: ...

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a given amount into the entity's account for a specific currency."""
        ...

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount from the entity's account for a specific currency.

        Raises:
            InsufficientFundsError: If the withdrawal amount exceeds available funds.
        """
        ...
```

### 3.2. `modules/government/proxy.py` (GovernmentFiscalProxy)

The proxy must be updated to correctly handle and pass the `currency` parameter.

**Current Implementation:**
```python
# modules/government/proxy.py

class GovernmentFiscalProxy(IFinancialEntity):
    # ... (init) ...
    @property
    def assets(self) -> float:
        return self._government.assets

    def deposit(self, amount: float) -> None:
        self._government.deposit(amount)

    def withdraw(self, amount: float) -> None:
        self._government.withdraw(amount)
    # ...
```

**Proposed Fix:**
```python
# modules/government/proxy.py

from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class GovernmentFiscalProxy(IFinancialEntity):
    # ... (init) ...
    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        return self._government.assets

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._government.deposit(amount, currency)

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._government.withdraw(amount, currency)
    # ...
```

### 3.3. `modules/system/escrow_agent.py` (EscrowAgent)

The `EscrowAgent` needs to be upgraded from a single float balance to a multi-currency dictionary to conform to the new interface.

**Current Implementation:**
```python
# modules/system/escrow_agent.py

class EscrowAgent(IFinancialEntity):
    def __init__(self, id: int):
        self._id = id
        self._assets = 0.0

    @property
    def assets(self) -> float:
        return self._assets

    def deposit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Deposit amount must be positive")
        self._assets += amount

    def withdraw(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Withdraw amount must be positive")
        if self._assets < amount:
            raise InsufficientFundsError(...)
        self._assets -= amount
```

**Proposed Fix:**
```python
# modules/system/escrow_agent.py

from collections import defaultdict
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class EscrowAgent(IFinancialEntity):
    def __init__(self, id: int):
        self._id = id
        self._balances: Dict[CurrencyCode, float] = defaultdict(float)

    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        return dict(self._balances)

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount < 0:
            raise ValueError("Deposit amount must be positive")
        self._balances[currency] += amount

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount < 0:
            raise ValueError("Withdraw amount must be positive")
        if self._balances[currency] < amount:
            raise InsufficientFundsError(f"EscrowAgent {self.id} has insufficient funds for {currency}. Needed: {amount}, Has: {self._balances[currency]}")
        self._balances[currency] -= amount
```

## 4. Affected Modules & Impact

-   **`simulation/base_agent.py` (`BaseAgent`, `Firm`, `Household`)**: No changes required. `BaseAgent` already uses `Wallet` and implements `deposit`/`withdraw` with the proposed signature.
-   **`simulation/agents/government.py` (`Government`)**: No changes required. Already compliant.
-   **`modules/system/execution/public_manager.py` (`PublicManager`)**: No changes required. Already compliant.
-   **`simulation/systems/settlement_system.py`**: This module heavily uses `IFinancialEntity`. While its internal logic might already handle multi-currency correctly, a thorough review and potential test updates will be necessary after this change to ensure calls to `deposit`/`withdraw` pass the correct currency.
-   **All Test Mocks**: Any test that uses a mock `IFinancialEntity` will need to be updated to match the new method signatures and the `assets` property return type.

This change is a prerequisite for robust multi-currency simulation and patches a potential source of significant data integrity issues.
