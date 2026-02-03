# Spec: Multi-Polar WorldState (Phase 33)

## 1. Overview & Goals

This document outlines the architectural changes required to transition the simulation from a single-currency, single-government model to a foundational multi-polar economic system. This is a preparatory phase focused on refactoring core data structures and interfaces.

**Primary Goals:**

1.  **Multi-Currency Asset Representation**: Modify all financial state representations (e.g., agent assets) from a single `float` to a dictionary mapping currency codes to floating-point values (`Dict[CurrencyCode, float]`).
2.  **Multi-Government Foundation**: Adapt `WorldState` and related components to support multiple, independent `Government` instances, paving the way for jurisdictional mechanics.
3.  **Maintain Diagnostic Integrity**: Ensure that critical diagnostic tools, specifically `trace_leak.py`, remain functional by providing a backward-compatible interface for querying total system money.

**Out of Scope for this Phase:**

*   Implementation of a currency exchange market or logic.
*   Implementation of a `JurisdictionSystem` to assign agents to specific governments.
*   Logic for cross-currency transactions.

## 2. Risk & Impact Audit: Mitigation Plan

This specification directly addresses the risks identified in the "Pre-flight Audit".

### 2.1. Mitigating God Class & SRP Violation (Risks 1 & 6)

To break the hardcoded dependency in `WorldState`'s money calculation methods and adhere to SRP/OCP, we will introduce a new interface.

**Action**:
- Create a new protocol, `ICurrencyHolder`, in `modules/system/api.py`.
- This protocol will have a single method: `get_assets_by_currency() -> Dict[CurrencyCode, float]`.
- All entities that hold money (`Household`, `Firm`, `Government`, `PublicManager`, `Bank`) **MUST** implement this interface.
- `WorldState` will no longer iterate through concrete agent lists for money calculation. Instead, it will iterate over a unified list of `ICurrencyHolder` instances. The `calculate_total_money` and `calculate_base_money` methods will be refactored to use this protocol, decoupling them from the specific agent types.

### 2.2. Managing Pervasive Data Model Changes (Risk 2)

The change from `assets: float` to `assets: Dict[CurrencyCode, float]` is the most impactful change.

**Action**:
- A new type alias `CurrencyCode = TypeAlias('str')` will be defined in `modules/system/api.py`.
- The `assets: float` attribute **MUST** be replaced with `assets: Dict[CurrencyCode, float]` in the following key DTOs and agent states:
    - `simulation.dtos.api.AgentStateData`
    - `modules.household.dtos.HouseholdStateDTO`
    - `simulation.dtos.firm_state_dto.FirmStateDTO`
    - `modules.government.dtos.GovernmentStateDTO`
    - And the internal state of `Household`, `Firm`, `Government`, `Bank`, `PublicManager`.

### 2.3. Resolving Government Ambiguity (Risk 3)

The system's assumption of a single government must be removed.

**Action**:
- `WorldState.government: Optional[Government]` **MUST** be changed to `WorldState.governments: List[Government]`.
- `WorldState.resolve_agent_id("GOVERNMENT")` will be **deprecated**. A warning should be logged if it is called. For temporary backward compatibility, it may return the ID of the first government in the list, but all call sites must be flagged for future refactoring.
- The `FiscalContext` DTO will remain unchanged for this phase to limit the refactoring scope. A future `JurisdictionSystem` will be responsible for creating a specific `FiscalContext` for each agent based on their location, but this is not part of the current work.

### 2.4. Enforcing Explicit Currency in Transactions (Risk 4)

All financial actions must be tagged with a currency.

**Action**:
- A mandatory `currency: CurrencyCode` field **MUST** be added to the following DTOs:
    - `simulation.dtos.api.TransactionData`
    - `simulation.dtos.api.OrderDTO`
    - `modules.finance.dtos.LoanDTO` (and related financial instruments)
- The price field in these DTOs (`price: float`) will now represent the price in the specified `currency`.

### 2.5. Ensuring Test Compatibility (Risk 5)

`trace_leak.py` and other diagnostic scripts must not break.

**Action**:
- The signatures of `WorldState.calculate_total_money` and `WorldState.calculate_base_money` **MUST** be changed to return `Dict[CurrencyCode, float]`.
- A new, dedicated method for diagnostics will be added to `WorldState`:
  ```python
  def get_total_system_money_for_diagnostics(self, target_currency: CurrencyCode = "USD") -> float:
      """
      Provides a single float value for total system money for backward compatibility
      with diagnostic tools. In a multi-currency world, this is an approximation.
      Current implementation sums the value of the target currency only.
      WARNING: This does not account for exchange rates.
      """
      # Implementation will call the refactored calculate_total_money()
      # and return the value for the specified currency.
      all_money = self.calculate_total_money()
      return all_money.get(target_currency, 0.0)
  ```
- `trace_leak.py` **MUST** be updated to call this new method.

## 3. Detailed Design & API Changes

### 3.1. `modules/system/api.py`

```python
from __future__ import annotations
from typing import Protocol, Dict, TypeAlias

CurrencyCode = TypeAlias('str')

class ICurrencyHolder(Protocol):
    """
    An interface for any entity that holds assets in one or more currencies.
    Used to decouple WorldState's money calculation from concrete agent types.
    """
    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        """Returns a dictionary of all assets held, keyed by currency code."""
        ...

# ... existing api.py content ...
```

### 3.2. `simulation/dtos/api.py` (Changes)

```python
from modules.system.api import CurrencyCode # New Import

@dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: int
    seller_id: int
    item_id: str
    quantity: float
    price: float
    currency: CurrencyCode  # ADDED
    market_id: str
    transaction_type: str

@dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: int
    agent_type: str
    assets: Dict[CurrencyCode, float] # CHANGED
    is_active: bool
    # ... other fields remain the same ...

@dataclass
class OrderDTO:
    agent_id: int
    item_id: str
    quantity: float
    price: float
    currency: CurrencyCode # ADDED
```

### 3.3. `simulation/world_state.py` (Changes)

```python
from __future__ import annotations
from typing import List, Dict, Any, Optional
# ... other imports
from modules.system.api import ICurrencyHolder, CurrencyCode # New Imports

class WorldState:
    """ ... """
    def __init__(...):
        # ...
        self.governments: List[Government] = [] # CHANGED
        # DEPRECATED self.government: Optional[Government] = None

        # NEW: List for unified money calculation
        self.currency_holders: List[ICurrencyHolder] = []
        # ...

    def calculate_base_money(self) -> Dict[CurrencyCode, float]:
        """
        Calculates M0 (Base Money) for each currency.
        M0 = Sum of all assets held by ICurrencyHolder implementations.
        """
        totals: Dict[CurrencyCode, float] = {}
        for holder in self.currency_holders:
            for currency, amount in holder.get_assets_by_currency().items():
                totals[currency] = totals.get(currency, 0.0) + amount
        return totals

    def calculate_total_money(self) -> Dict[CurrencyCode, float]:
        """
        Calculates M2 (Total Money Supply) for each currency.
        M2 = Currency in Circulation + Deposits.
        Refactored to use ICurrencyHolder.
        """
        # Note: The logic for distinguishing M0 from M2 (i.e., handling deposits)
        # will need careful implementation within the Bank's get_assets_by_currency method.
        # For M2, the bank should report deposits, not reserves. For M0, it reports reserves.
        # This spec assumes calculate_base_money is the primary method for now.
        # The exact implementation will depend on how Bank implements ICurrencyHolder.
        # For now, we assume a simple sum as a placeholder for the logic.
        return self.calculate_base_money() # Placeholder for more complex M2 logic

    def get_total_system_money_for_diagnostics(self, target_currency: CurrencyCode = "USD") -> float:
        """
        Provides a single float value for total system money for backward compatibility
        with diagnostic tools.
        WARNING: This does not account for exchange rates and only tracks one currency.
        """
        all_money = self.calculate_total_money()
        return all_money.get(target_currency, 0.0)

    def resolve_agent_id(self, role: str) -> Optional[int]:
        """
        DEPRECATED. Use a JurisdictionSystem for multi-government contexts.
        """
        if role == "GOVERNMENT":
            self.logger.warning("Call to deprecated method WorldState.resolve_agent_id('GOVERNMENT')")
            if self.governments:
                return self.governments[0].id
            return None
        # ...
```

## 4. Verification Plan

1.  **Refactoring**: Update all DTOs and agent classes listed in section 2.2 to use `Dict[CurrencyCode, float]` for assets.
2.  **Implementation**: All money-holding entities must implement the `ICurrencyHolder` interface.
3.  **Unit Tests**:
    - All existing tests related to agent assets and transactions must be updated to handle the new data structure.
    - New tests must be written for `WorldState.calculate_base_money` and `WorldState.calculate_total_money` to verify correct aggregation across multiple currencies and multiple agents.
4.  **Integration Test**:
    - The `trace_leak.py` script must be modified to use `get_total_system_money_for_diagnostics`.
    - A full simulation run must complete without money-leak errors reported by the updated `trace_leak.py` (when tracking a single, primary currency).
5.  **Code Review**: All changes must be reviewed to ensure no `assets: float` fields remain and that all new transactions are currency-aware.

---

## 5. Insight & Technical Debt Ledger

-   **TD-PH33-01**: The `FiscalContext` DTO remains coupled to a single government entity. This is a deliberate simplification for this phase but will need to be addressed by a future `JurisdictionSystem` that provides context-specific fiscal information to agents.
-   **TD-PH33-02**: The `get_total_system_money_for_diagnostics` method is a compatibility layer that provides an incomplete view of the system's economy. It does not account for exchange rates. It should be removed once all diagnostic tools are fully multi-currency aware.
-   **INSIGHT-PH33-01**: The introduction of `ICurrencyHolder` significantly improves the design by adhering to the Open/Closed Principle. Adding new types of money-holding entities in the future will not require modifying `WorldState`.
