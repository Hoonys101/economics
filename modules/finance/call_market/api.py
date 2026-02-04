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
    def clear_market(self, tick: int) -> MarketClearingResultDTO:
        """
        Matches buy (request) and sell (offer) orders to clear the market.

        This process determines the clearing interest rate and the volume of
        loans transacted for the session. It should be called once per cycle
        after all bids and offers have been submitted.

        Args:
            tick: The current simulation tick, used for loan origination time.

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
    def settle_matured_loans(self, tick: int) -> None:
        """
        Processes loans that have reached their maturity date.

        This involves transferring the principal and accrued interest from the
        borrower's reserve account back to the lender's reserve account.

        Args:
            tick: The current simulation tick, used to check loan maturity.
        """
        ...
