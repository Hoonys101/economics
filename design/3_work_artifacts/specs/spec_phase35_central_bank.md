I will now create the two `api.py` files and the `spec.md` file as requested.

First, `modules/finance/central_bank/api.py`:
I will now create the two `api.py` files and the `spec.md` file as requested.

First, `modules/finance/central_bank/api.py`:

```python
# --- modules/finance/central_bank/api.py ---
from __future__ import annotations
from typing import Protocol, TypedDict, Literal, List, TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    # This service is expected to be defined in a government module,
    # managing the issuance and market for government securities.
    # This is a forward reference to avoid circular imports.
    from modules.government.treasury.api import ITreasuryService, BondDTO

# ==============================================================================
# Data Transfer Objects (DTOs)
# ==============================================================================

class PolicyRateDTO(TypedDict):
    """
    Represents the central bank's policy interest rate.
    This is a pure data object for inter-system communication.
    """
    rate: float
    effective_tick: int
    decision_tick: int

class OpenMarketOperationResultDTO(TypedDict):
    """
    Summarizes the outcome of an open market operation, ensuring a clear
    record of the transaction for auditing and analysis.
    """
    success: bool
    operation_type: Literal["purchase", "sale"]
    bonds_transacted_count: int
    cash_transferred: float
    message: str

# ==============================================================================
# Exceptions
# ==============================================================================

class InvalidPolicyRateError(Exception):
    """Raised when an attempt is made to set an invalid policy rate (e.g., negative)."""
    pass

class TreasuryServiceError(Exception):
    """
    Raised when an interaction with the ITreasuryService fails, for example,
    if there are not enough bonds available for purchase.
    """
    pass

# ==============================================================================
# Interface
# ==============================================================================

class ICentralBank(Protocol):
    """
    Defines the contract for the Central Bank, responsible for monetary policy
    execution. Its primary levers are the policy rate and open market operations,
    which are used to influence the money supply and steer market rates.
    """

    @abstractmethod
    def set_policy_rate(self, rate: float) -> PolicyRateDTO:
        """
        Sets the main policy interest rate for the economy.

        This rate acts as a crucial benchmark for the entire financial system,
        heavily influencing inter-bank lending rates (e.g., in the call market)
        and subsequent commercial lending rates to firms and households.

        Args:
            rate: The new policy interest rate (e.g., 0.05 for 5%).

        Returns:
            A DTO confirming the new rate and the tick it becomes effective.

        Raises:
            InvalidPolicyRateError: If the provided rate is outside a valid range.
        """
        ...

    @abstractmethod
    def get_policy_rate(self) -> PolicyRateDTO:
        """
        Retrieves the current policy interest rate.

        Returns:
            A DTO containing the current rate information.
        """
        ...

    @abstractmethod
    def conduct_open_market_operation(
        self,
        treasury_service: "ITreasuryService",
        operation_type: Literal["purchase", "sale"],
        target_cash_amount: float
    ) -> OpenMarketOperationResultDTO:
        """
        Executes open market operations by buying or selling government bonds.

        - 'purchase': The central bank buys bonds from commercial banks,
                      injecting cash (reserves) into the banking system.
        - 'sale': The central bank sells bonds to commercial banks,
                  withdrawing cash (reserves) from the banking system.

        This is the primary mechanism for managing the level of reserves in the
        banking system to keep the inter-bank lending rate close to the policy rate.

        Args:
            treasury_service: The interface for accessing the government bond market.
            operation_type: The type of operation to execute ('purchase' or 'sale').
            target_cash_amount: The total cash value of bonds to be transacted.

        Returns:
            A DTO summarizing the result of the operation.

        Raises:
            TreasuryServiceError: If the treasury service cannot fulfill the request.
        """
        ...
```

Second, `modules/finance/call_market/api.py`:

```python
# --- modules/finance/call_market/api.py ---
from __future__ import annotations
from typing import Protocol, TypedDict, List, Optional
from abc import abstractmethod

# ==============================================================================
# Data Transfer Objects (DTOs)
# ==============================================================================

class CallLoanRequestDTO(TypedDict):
    """
    A request from a commercial bank to borrow reserves.
    """
    borrower_id: int
    amount: float
    max_interest_rate: float # The highest rate the borrower is willing to pay.

class CallLoanOfferDTO(TypedDict):
    """
    An offer from a commercial bank to lend reserves.
    """
    lender_id: int
    amount: float
    min_interest_rate: float # The lowest rate the lender is willing to accept.

class CallLoanDTO(TypedDict):
    """
    Represents a successfully matched loan in the call market.
    This is an immutable record of a completed transaction.
    """
    loan_id: str
    lender_id: int
    borrower_id: int
    amount: float
    interest_rate: float
    origination_tick: int
    maturity_tick: int

class MarketClearingResultDTO(TypedDict):
    """
    Summarizes the state of the market after a clearing event.
    """
    cleared_volume: float
    weighted_average_rate: float
    matched_loans: List[CallLoanDTO]

# ==============================================================================
# Exceptions
# ==============================================================================

class InsufficientReservesError(Exception):
    """Raised if a bank attempts to offer a loan with reserves it does not have."""
    pass

# ==============================================================================
# Interface
# ==============================================================================

class ICallMarket(Protocol):
    """
    Defines the contract for the Call Market, an inter-bank market for short-term
    (typically overnight) lending and borrowing of reserves.

    This market is crucial for banks to manage their daily liquidity needs and
    meet reserve requirements. The interest rate in this market is a key
    target of central bank monetary policy.
    """

    @abstractmethod
    def submit_loan_request(self, request: CallLoanRequestDTO) -> None:
        """
        A bank submits a bid to borrow reserves.

        Args:
            request: A DTO containing the details of the borrowing request.
        """
        ...

    @abstractmethod
    def submit_loan_offer(self, offer: CallLoanOfferDTO) -> None:
        """
        A bank submits an offer to lend reserves.

        Args:
            offer: A DTO containing the details of the lending offer.

        Raises:
            InsufficientReservesError: If the lending bank does not have enough
                                       reserves to cover the offer.
        """
        ...

    @abstractmethod
    def clear_market(self) -> MarketClearingResultDTO:
        """
        Matches buy (request) and sell (offer) orders to clear the market.

        This process determines the clearing interest rate and the volume of
        loans transacted for the session. It should be called once per cycle
        after all bids and offers have been submitted.

        Returns:
            A DTO summarizing the loans that were matched and the market rate.
        """
        ...

    @abstractmethod
    def get_market_rate(self) -> float:
        """
        Retrieves the last calculated weighted average interest rate for the market.

        Returns:
            The interest rate from the last market clearing. Returns a default or
            last known value if the market has not cleared yet.
        """
        ...

    @abstractmethod
    def settle_matured_loans(self) -> None:
        """
        Processes loans that have reached their maturity date.

        This involves transferring the principal and accrued interest from the
        borrower's reserve account back to the lender's reserve account.
        """
        ...
```

Third, `design/3_work_artifacts/specs/phase5_monetary_policy_spec.md`:

```markdown
# Spec: Phase 5 - Monetary Policy Engine
**Domain**: Finance
**Author**: Gemini (Scribe)
**Status**: Draft

## 1. Overview & Goals
This specification details the architecture for two core components of the monetary system: `ICentralBank` and `ICallMarket`. The goal is to establish a framework where the central bank can implement monetary policy, influencing the economy by setting a policy rate and managing liquidity, with the effects propagating through an inter-bank lending market.

This system directly integrates with the `ITreasuryService` for conducting open market operations.

## 2. Component: `ICentralBank`
The `ICentralBank` is the primary agent of monetary policy. It has two main tools: setting the policy rate and conducting Open Market Operations (OMO).

### 2.1. API & DTOs
- **`ICentralBank(Protocol)`**:
  - `set_policy_rate(rate: float) -> PolicyRateDTO`
  - `get_policy_rate() -> PolicyRateDTO`
  - `conduct_open_market_operation(...) -> OpenMarketOperationResultDTO`
- **DTOs**:
  - `PolicyRateDTO`: `{rate: float, effective_tick: int, decision_tick: int}`
  - `OpenMarketOperationResultDTO`: `{success: bool, operation_type: Literal, ...}`

### 2.2. Logic (Pseudo-code)

#### `set_policy_rate`
```pseudo
FUNCTION set_policy_rate(rate):
  IF rate < 0:
    RAISE InvalidPolicyRateError("Rate cannot be negative")
  
  self.state.policy_rate = rate
  self.state.effective_tick = current_tick + 1
  
  RETURN PolicyRateDTO(rate=rate, effective_tick=self.state.effective_tick, ...)
```

#### `conduct_open_market_operation`
This function is the bridge to the `ITreasuryService`.
```pseudo
FUNCTION conduct_open_market_operation(treasury_service, type, amount):
  // 1. Central Bank requests to buy or sell bonds from the Treasury Service
  //    The treasury service is assumed to handle the transaction with the market (commercial banks)
  IF type == "purchase":
    // CB wants to inject money. It buys bonds from commercial banks.
    // The treasury_service finds sellers and facilitates the transfer.
    // The result includes the cash transferred and bonds exchanged.
    result = treasury_service.execute_market_purchase(
        buyer_id="CENTRAL_BANK", 
        target_cash_amount=amount
    )
  ELSE: // "sale"
    // CB wants to remove money. It sells its own bond holdings to commercial banks.
    result = treasury_service.execute_market_sale(
        seller_id="CENTRAL_BANK",
        target_cash_amount=amount
    )

  // 2. The transaction settlement (handled by a SettlementSystem) will move cash
  //    between the commercial banks and the central bank, thus changing the
  //    total reserves in the banking system.
  
  IF result.success == FALSE:
    RAISE TreasuryServiceError(result.message)

  RETURN OpenMarketOperationResultDTO(
      success=true,
      bonds_transacted_count=result.bonds_exchanged,
      cash_transferred=result.cash_exchanged,
      ...
  )
```

### 2.3. Exception Handling
- `InvalidPolicyRateError`: Thrown if `set_policy_rate` receives a negative value.
- `TreasuryServiceError`: Thrown if `conduct_open_market_operation` fails because the `ITreasuryService` cannot execute the trade (e.g., no bonds available to purchase).

## 3. Component: `ICallMarket`
The `ICallMarket` is where commercial banks lend and borrow reserves among themselves on a short-term basis. The interest rate here (`call_rate`) is heavily influenced by the supply of reserves, which is controlled by the `ICentralBank`.

### 3.1. API & DTOs
- **`ICallMarket(Protocol)`**:
  - `submit_loan_request(request: CallLoanRequestDTO)`
  - `submit_loan_offer(offer: CallLoanOfferDTO)`
  - `clear_market() -> MarketClearingResultDTO`
  - `get_market_rate() -> float`
  - `settle_matured_loans()`
- **DTOs**:
  - `CallLoanRequestDTO`: `{borrower_id: int, amount: float, max_interest_rate: float}`
  - `CallLoanOfferDTO`: `{lender_id: int, amount: float, min_interest_rate: float}`
  - `CallLoanDTO`: `{loan_id: str, lender_id: int, borrower_id: int, ...}`
  - `MarketClearingResultDTO`: `{cleared_volume: float, weighted_average_rate: float, ...}`

### 3.2. Logic (Pseudo-code)

#### `clear_market`
```pseudo
FUNCTION clear_market():
  // 1. Get all submitted offers and requests for the current tick.
  offers = self.get_pending_offers() // -> List[CallLoanOfferDTO]
  requests = self.get_pending_requests() // -> List[CallLoanRequestDTO]

  // 2. Sort orders to facilitate matching.
  SORT offers by min_interest_rate ASCENDING
  SORT requests by max_interest_rate DESCENDING

  matched_loans = []
  total_volume = 0
  total_rate_volume = 0

  // 3. Iterate and match.
  offer_idx = 0
  request_idx = 0
  WHILE offer_idx < len(offers) AND request_idx < len(requests):
    current_offer = offers[offer_idx]
    current_request = requests[request_idx]

    // Condition to match: borrower's max rate is >= lender's min rate
    IF current_request.max_interest_rate >= current_offer.min_interest_rate:
      // Match found. Determine clearing rate and volume.
      clearing_rate = (current_request.max_interest_rate + current_offer.min_interest_rate) / 2
      clearing_volume = min(current_offer.amount, current_request.amount)
      
      // Create the loan record.
      loan = create_loan_dto(
          lender=current_offer.lender_id,
          borrower=current_request.borrower_id,
          amount=clearing_volume,
          rate=clearing_rate
      )
      matched_loans.append(loan)

      // Update aggregates
      total_volume += clearing_volume
      total_rate_volume += clearing_volume * clearing_rate

      // Update amounts and advance indices
      current_offer.amount -= clearing_volume
      current_request.amount -= clearing_volume
      IF current_offer.amount == 0:
        offer_idx += 1
      IF current_request.amount == 0:
        request_idx += 1
    ELSE:
      // No match possible at this price point.
      BREAK

  // 4. Trigger settlement for the newly created loans via SettlementSystem.
  //    This will move reserves between the banks' accounts.
  settlement_system.settle_call_loans(matched_loans)
  
  // 5. Return summary
  avg_rate = total_rate_volume / total_volume IF total_volume > 0 ELSE 0
  RETURN MarketClearingResultDTO(
      cleared_volume=total_volume,
      weighted_average_rate=avg_rate,
      matched_loans=matched_loans
  )
```

### 3.3. Exception Handling
- `InsufficientReservesError`: Thrown if a bank calls `submit_loan_offer` with an amount greater than its available reserves. This check must happen before the offer is accepted by the market.

## 4. Verification & Mocking

### 4.1. Golden Data & Mock Strategy
- **`ITreasuryService` Mock**: A mock implementation of `ITreasuryService` is essential. It should have a predictable inventory of bonds and be able to simulate successful and failed purchase/sale operations.
- **Commercial Bank Fixtures**: Tests should use `golden_firms` or similar fixtures to represent commercial banks. These fixtures must be initialized with a `wallet` and a `reserve_account`.
  - **Setup**: `tests/conftest.py` will need to be extended to ensure test banks have a starting quantity of reserves.
- **Scenario Testing**:
  1. **Liquidity Squeeze**: Test a scenario where `ICentralBank` performs a bond `sale`, draining reserves. Verify that the `call_rate` in `ICallMarket` rises as a result.
  2. **Liquidity Glut**: Test a scenario where `ICentralBank` performs a bond `purchase`, injecting reserves. Verify that the `call_rate` falls.
  3. **No Match**: Test `clear_market` when `max_interest_rate` of all requests is below `min_interest_rate` of all offers. Verify `cleared_volume` is 0.

### 4.2. Schema Change Notice
- Any change to `BondDTO` in the `ITreasuryService` will require updating the mock `ITreasuryService` and any related test fixtures.

## 5. Risk & Impact Audit

- **[High] Circular Dependency**: `ICentralBank` depends on `ITreasuryService`. Care must be taken to ensure that `ITreasuryService` does not have a hard dependency back on `ICentralBank` within the same transaction tick, as this could cause a deadlock or infinite loop. The dependency should be one-way: `CentralBank -> TreasuryService`.
- **[Medium] Test Impact**: Existing tests for commercial banks that only model a simple `wallet` will need to be updated. The concept of `reserves` vs. `deposits` must be clearly delineated, and bank tests must account for reserve changes from call market and OMO activities.
- **[Low] Configuration Dependency**: `economy_params.yaml` will need new entries:
  - `central_bank.initial_policy_rate`
  - `call_market.loan_duration_ticks` (e.g., 1 for overnight)
- **[Medium] Settlement Logic**: The design assumes a `SettlementSystem` is responsible for the atomic transfer of reserves and bonds. The implementation of this system is critical. A failure in settlement would break the entire monetary engine. The interfaces for settlement must be robust.
- **[Recommendation] Precedent Task**: Before implementing `conduct_open_market_operation`, the `ITreasuryService` API must be finalized and a stable mock implementation must be available.
```
