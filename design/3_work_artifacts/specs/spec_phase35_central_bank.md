# Spec: Central Bank & Call Market (Phase 5)

## 1. Overview
This document specifies the architecture for Phase 5, introducing key monetary policy instruments. It defines the interfaces for a central bank (`ICentralBank`) responsible for setting the policy rate and conducting open market operations, and a call market (`ICallMarket`) for inter-agent reserve lending. This design integrates with the `ITreasuryService` to ensure a cohesive financial system.

## 2. Core Components

### 2.1. `ICentralBank`
- **Responsibility**: Manages the economy's base interest rate and influences liquidity by transacting with the Treasury.
- **Key Functions**: Setting the policy rate, buying/selling government bonds.

### 2.2. `ICallMarket`
- **Responsibility**: Facilitates short-term (e.g., single-tick) lending and borrowing of base reserves between financial agents (e.g., Firms).
- **Key Functions**: Matching lenders with borrowers, determining the market-clearing call rate based on supply, demand, and the policy rate.

### 2.3. `ITreasuryService` (External Dependency)
- **Responsibility**: Manages government debt and finances.
- **Assumed Interface**: Must provide a mechanism for the Central Bank to purchase bonds (`sell_bonds_to_central_bank`).

## 3. Interface & DTO Definitions

```python
# In: modules/finance/api.py

from typing import Protocol, TypedDict, Optional

# --- DTOs for Data Transfer ---

class PolicyRateDTO(TypedDict):
    """Data Transfer Object for the policy interest rate."""
    rate: float
    tick: int

class OpenMarketOperationResultDTO(TypedDict):
    """Result of an open market operation."""
    success: bool
    bonds_transacted: int
    cash_transferred: float
    message: str

class CallLoanRequestDTO(TypedDict):
    """Request from an agent to borrow from the call market."""
    borrower_id: str
    amount: float

class CallLoanResponseDTO(TypedDict):
    """Response to a call loan request."""
    success: bool
    loan_id: Optional[str]
    amount_granted: float
    interest_rate: float
    message: str

class TreasurySaleResponseDTO(TypedDict):
    """A generic response from the Treasury for a sales operation."""
    success: bool
    details: str

# --- Interfaces (Protocols) ---

class ITreasuryService(Protocol):
    """
    Assumed interface for the Treasury. The Central Bank will interact with this
    to conduct open market operations.
    """
    def sell_bonds_to_central_bank(self, quantity: int, price: float) -> TreasurySaleResponseDTO:
        """Sells a specified quantity of bonds to the central bank."""
        ...

class ICentralBank(Protocol):
    """
    Interface for the central monetary authority.
    """
    def set_policy_rate(self, rate: float, tick: int) -> None:
        """
        Sets the base policy interest rate for the economy.
        This is a key lever for monetary policy.
        """
        ...

    def get_policy_rate(self) -> PolicyRateDTO:
        """Retrieves the current policy rate."""
        ...

    def conduct_open_market_operations(
        self,
        treasury: ITreasuryService,
        quantity_to_buy: int
    ) -> OpenMarketOperationResultDTO:
        """
        Injects liquidity by purchasing bonds from the treasury.
        A negative quantity would signify selling bonds to withdraw liquidity.
        """
        ...


class ICallMarket(Protocol):
    """
    Interface for the short-term inter-agent lending market.
    """
    def request_loan(self, request: CallLoanRequestDTO) -> CallLoanResponseDTO:
        """An agent requests a loan for the current tick."""
        ...

    def supply_reserves(self, lender_id: str, amount: float) -> None:
        """An agent supplies reserves to the market for lending."""
        ...

    def process_market_clearing(self, policy_rate: float) -> float:
        """
        Matches lenders and borrowers, calculates the call rate, and executes loans.
        This should be called once per tick by the simulation engine.
        Returns the calculated market-clearing call rate for the tick.
        """
        ...
```

## 4. Logic Steps (Pseudo-code)

### 4.1. `ICentralBank.conduct_open_market_operations`
1.  Determine the target quantity of bonds to buy or sell.
2.  Query a market module (TBD) for the current price of government bonds. If unavailable, use face value.
3.  Call `treasury.sell_bonds_to_central_bank(quantity, price)`.
4.  If the treasury operation is successful:
    a.  Debit the Central Bank's cash reserves by `quantity * price`.
    b.  Credit the Central Bank's bond assets by `quantity`.
    c.  Credit the Treasury's cash account (and by extension, the reserves in the system).
5.  Return an `OpenMarketOperationResultDTO` detailing the transaction.

### 4.2. `ICallMarket.process_market_clearing`
1.  Sum the total reserves supplied by all lenders for the current tick.
2.  Sum the total loan amounts requested by all borrowers.
3.  Calculate the liquidity ratio: `liquidity_ratio = total_supplied / total_requested`.
4.  Define a spread based on demand. E.g., `spread = max(0, (1 - liquidity_ratio) * SPREAD_SENSITIVITY_PARAM)`.
5.  Calculate the market-clearing call rate: `call_rate = policy_rate + spread`.
6.  **If `liquidity_ratio >= 1` (Sufficient Funds):**
    a.  Iterate through all loan requests.
    b.  Grant each loan in full at the calculated `call_rate`.
    c.  Create a loan record (due next tick).
    d.  Update lender and borrower balance sheets.
7.  **If `liquidity_ratio < 1` (Insufficient Funds):**
    a.  Iterate through all loan requests.
    b.  Grant a prorated loan amount: `amount_granted = request.amount * liquidity_ratio`.
    c.  Create loan records for the prorated amounts at the calculated `call_rate`.
    d.  Update balance sheets.
8.  Return the calculated `call_rate`.
9.  Clear all supplied reserves and pending requests for the next tick.

## 5. Exception Handling
- **`ICentralBank`**:
  - `TreasuryOperationError`: Raised if `treasury.sell_bonds_to_central_bank` returns `success: false`. The OMO fails.
- **`ICallMarket`**:
  - `InsufficientLiquidityError`: While not an exception that stops the process, the log should clearly state when demand exceeds supply and loans are prorated.
  - `InvalidAgentIDError`: Raised if a `borrower_id` or `lender_id` does not exist in the agent registry.

## 6. Verification Plan
- **Unit Tests**:
  - `test_central_bank_set_rate`: Verify `set_policy_rate` updates the internal state correctly.
  - `test_call_market_clearing_sufficient_liquidity`: Scenario where supply >= demand. Verify all loans are granted and `call_rate` is close to `policy_rate`.
  - `test_call_market_clearing_insufficient_liquidity`: Scenario where supply < demand. Verify loans are prorated and `call_rate` is significantly higher than `policy_rate`.
- **Integration Test (`test_monetary_policy_channel`)**:
  1.  Setup: Use `golden_firms` fixture. Designate 2 firms as lenders, 2 as borrowers.
  2.  Action 1: `ICentralBank.set_policy_rate(0.05)`.
  3.  Action 2: Lenders supply reserves to `ICallMarket`. Borrowers request loans.
  4.  Action 3: `ICallMarket.process_market_clearing()`.
  5.  Assert: Verify the final `call_rate` and that balance sheets were updated correctly.
  6.  Action 4: `ICentralBank.conduct_open_market_operations(treasury_mock, quantity_to_buy=1000)`.
  7.  Action 5: Rerun `ICallMarket.process_market_clearing()` with the same requests.
  8.  Assert: The increased system liquidity should lower the new `call_rate` compared to the previous one.

## 7. Mocking Guide
- **`ITreasuryService`**: For all unit and most integration tests, a mock implementation of `ITreasuryService` will be required. This mock should simply return `success: true` and allow inspection of the `quantity` and `price` it was called with.
- **Agents**: All participating agents (lenders, borrowers) will be drawn from the `golden_firms` and `golden_households` conftest fixtures. **DO NOT** use `MagicMock()` to create new agents, as this breaks type contracts and validation.
- **Custom Scenarios**: If a test requires a specific agent balance sheet that is not in the golden set, use `scripts/fixture_harvester.py`'s `GoldenLoader` to load a specific snapshot.

## 8. 🚨 Schema Change Notice
The introduction of `PolicyRateDTO`, `CallLoanRequestDTO`, etc., constitutes a schema change. If the state of the call market or central bank needs to be persisted in simulation snapshots, the `fixture_harvester.py` script and its underlying schemas may need to be updated to recognize these new objects.

## 9. 🚨 Risk & Impact Audit (Technology Risk Analysis)
- **Circular Dependency Risk**: `modules.finance` (this spec) will have a dependency on `modules.government.treasury` (via `ITreasuryService`). The implementation must ensure that `treasury` does not, in turn, import from `finance` to avoid a circular import. The dependency must be one-way.
- **Test Impact**: Existing integration tests that run the full simulation loop will fail without a concrete implementation of `ICentralBank` and `ICallMarket` being provided to the simulation runner. A default "do-nothing" implementation may be required to prevent breaking unrelated tests.
- **Configuration Dependency**: The simulation will require new parameters in `economy_params.yaml`, such as `initial_policy_rate` and `call_market_spread_sensitivity`. The implementation must handle the absence of these configs gracefully (e.g., by using default values) but log a clear warning.
- **Precedent Work**: This entire feature is blocked until `ITreasuryService` and its `sell_bonds_to_central_bank` method are defined and implemented in Thread 1. The contract must be agreed upon and finalized before implementation begins.

---
*Generated by Scribe-Assistant. Ready for `gemini_worker.py`.*
---
```python
# Path: modules/finance/api.py
from typing import Protocol, TypedDict, Optional, List

# --- DTOs for Data Transfer ---

class PolicyRateDTO(TypedDict):
    """Data Transfer Object for the policy interest rate."""
    rate: float
    tick: int

class OpenMarketOperationResultDTO(TypedDict):
    """Result of an open market operation."""
    success: bool
    bonds_transacted: int
    cash_transferred: float
    message: str

class CallLoanRequestDTO(TypedDict):
    """Request from an agent to borrow from the call market."""
    borrower_id: str
    amount: float

class CallLoanResponseDTO(TypedDict):
    """Response to a call loan request."""
    success: bool
    loan_id: Optional[str]
    amount_granted: float
    interest_rate: float
    message: str

class TreasurySaleResponseDTO(TypedDict):
    """A generic response from the Treasury for a sales operation."""
    success: bool
    details: str

# --- Interfaces (Protocols) ---

class ITreasuryService(Protocol):
    """
    Assumed interface for the Treasury. The Central Bank will interact with this
    to conduct open market operations.
    """
    def sell_bonds_to_central_bank(self, quantity: int, price: float) -> TreasurySaleResponseDTO:
        """Sells a specified quantity of bonds to the central bank."""
        ...

class ICentralBank(Protocol):
    """
    Interface for the central monetary authority.
    """
    def set_policy_rate(self, rate: float, tick: int) -> None:
        """
        Sets the base policy interest rate for the economy.
        This is a key lever for monetary policy.
        """
        ...

    def get_policy_rate(self) -> PolicyRateDTO:
        """Retrieves the current policy rate."""
        ...

    def conduct_open_market_operations(
        self,
        treasury: ITreasuryService,
        quantity_to_buy: int
    ) -> OpenMarketOperationResultDTO:
        """
        Injects liquidity by purchasing bonds from the treasury.
        A negative quantity would signify selling bonds to withdraw liquidity.
        """
        ...


class ICallMarket(Protocol):
    """
    Interface for the short-term inter-agent lending market.
    """
    def request_loan(self, request: CallLoanRequestDTO) -> CallLoanResponseDTO:
        """An agent requests a loan for the current tick."""
        ...

    def supply_reserves(self, lender_id: str, amount: float) -> None:
        """An agent supplies reserves to the market for lending."""
        ...

    def process_market_clearing(self, policy_rate: float) -> float:
        """
        Matches lenders and borrowers, calculates the call rate, and executes loans.
        This should be called once per tick by the simulation engine.
        Returns the calculated market-clearing call rate for the tick.
        """
        ...
```
