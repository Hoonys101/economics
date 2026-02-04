from __future__ import annotations
import uuid
import logging
from typing import List, Dict, Any, Optional

from modules.finance.call_market.api import (
    ICallMarket,
    CallLoanRequestDTO,
    CallLoanOfferDTO,
    CallLoanDTO,
    MarketClearingResultDTO,
    InsufficientReservesError,
)
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry, DEFAULT_CURRENCY

class CallMarketService(ICallMarket):
    """
    Implementation of the Inter-bank Call Market.
    Matches short-term reserve lending and borrowing between banks.
    """

    def __init__(
        self,
        settlement_system: ISettlementSystem,
        agent_registry: IAgentRegistry,
        config_module: Any,
        logger: Optional[logging.Logger] = None
    ):
        self.settlement_system = settlement_system
        self.agent_registry = agent_registry
        self.config_module = config_module
        self.logger = logger or logging.getLogger(__name__)

        self.pending_requests: List[CallLoanRequestDTO] = []
        self.pending_offers: List[CallLoanOfferDTO] = []
        self.active_loans: Dict[str, CallLoanDTO] = {}
        self.last_clearing_rate: float = 0.0

        # Configuration
        self.ticks_per_year = float(getattr(self.config_module, "TICKS_PER_YEAR", 100.0))
        # Default loan duration is overnight (1 tick) unless specified otherwise.
        self.loan_duration = int(getattr(self.config_module, "CALL_MARKET_LOAN_DURATION", 1))

    def submit_loan_request(self, request: CallLoanRequestDTO) -> None:
        """
        A bank submits a bid to borrow reserves.
        """
        if request['amount'] <= 0:
            self.logger.warning(f"CallMarket: Invalid request amount {request['amount']} from {request['borrower_id']}")
            return

        self.pending_requests.append(request)
        self.logger.debug(f"CallMarket: Request received from {request['borrower_id']} for {request['amount']} @ max {request['max_interest_rate']:.4f}")

    def submit_loan_offer(self, offer: CallLoanOfferDTO) -> None:
        """
        A bank submits an offer to lend reserves.
        Checks if the lender has sufficient reserves.
        """
        if offer['amount'] <= 0:
            self.logger.warning(f"CallMarket: Invalid offer amount {offer['amount']} from {offer['lender_id']}")
            return

        lender = self.agent_registry.get_agent(offer['lender_id'])
        if not lender:
            self.logger.error(f"CallMarket: Lender {offer['lender_id']} not found in registry.")
            # We can't verify reserves, but preventing offer is safer.
            raise InsufficientReservesError(f"Lender {offer['lender_id']} not found.")

        # Check reserves
        current_reserves = 0.0
        if hasattr(lender, 'wallet'):
            current_reserves = lender.wallet.get_balance(DEFAULT_CURRENCY)
        else:
            # Fallback for mock agents or legacy structure
             try:
                 assets = getattr(lender, 'assets', 0.0)
                 if isinstance(assets, dict):
                     current_reserves = assets.get(DEFAULT_CURRENCY, 0.0)
                 else:
                     current_reserves = float(assets)
             except (ValueError, TypeError):
                 current_reserves = 0.0

        if current_reserves < offer['amount']:
            raise InsufficientReservesError(
                f"Lender {offer['lender_id']} has insufficient reserves. "
                f"Required: {offer['amount']}, Available: {current_reserves}"
            )

        self.pending_offers.append(offer)
        self.logger.debug(f"CallMarket: Offer received from {offer['lender_id']} for {offer['amount']} @ min {offer['min_interest_rate']:.4f}")

    def clear_market(self, tick: int) -> MarketClearingResultDTO:
        """
        Matches buy (request) and sell (offer) orders to clear the market.
        """
        # 1. Sort orders
        # Offers: Ascending by min_rate (cheapest first)
        sorted_offers = sorted(self.pending_offers, key=lambda x: x['min_interest_rate'])
        # Requests: Descending by max_rate (willing to pay most first)
        sorted_requests = sorted(self.pending_requests, key=lambda x: x['max_interest_rate'], reverse=True)

        matched_loans: List[CallLoanDTO] = []
        total_volume = 0.0
        total_rate_volume = 0.0

        offer_idx = 0
        request_idx = 0

        while offer_idx < len(sorted_offers) and request_idx < len(sorted_requests):
            offer = sorted_offers[offer_idx]
            request = sorted_requests[request_idx]

            # Matching condition: Borrower is willing to pay at least what Lender asks
            if request['max_interest_rate'] >= offer['min_interest_rate']:
                # Match found

                # Determine Clearing Rate: Midpoint
                # (As per spec pseudo-code)
                clearing_rate = (request['max_interest_rate'] + offer['min_interest_rate']) / 2.0

                # Determine Volume
                match_amount = min(offer['amount'], request['amount'])

                # Execute Settlement (Principal Transfer)
                lender = self.agent_registry.get_agent(offer['lender_id'])
                borrower = self.agent_registry.get_agent(request['borrower_id'])

                if lender and borrower:
                    memo = f"CallMarket Loan {offer['lender_id']}->{request['borrower_id']} @ {clearing_rate:.4f}"

                    # Call Settlement System
                    tx = self.settlement_system.transfer(
                        debit_agent=lender,
                        credit_agent=borrower,
                        amount=match_amount,
                        memo=memo,
                        tick=tick,
                        currency=DEFAULT_CURRENCY
                    )

                    if tx:
                        # Success
                        loan_id = str(uuid.uuid4())
                        loan_dto = CallLoanDTO(
                            loan_id=loan_id,
                            lender_id=offer['lender_id'],
                            borrower_id=request['borrower_id'],
                            amount=match_amount,
                            interest_rate=clearing_rate,
                            origination_tick=tick,
                            maturity_tick=tick + self.loan_duration
                        )

                        matched_loans.append(loan_dto)
                        self.active_loans[loan_id] = loan_dto

                        total_volume += match_amount
                        total_rate_volume += match_amount * clearing_rate

                        # Update remaining amounts
                        offer['amount'] -= match_amount
                        request['amount'] -= match_amount

                    else:
                        self.logger.error(
                            f"CallMarket: Settlement failed for match {offer['lender_id']} -> {request['borrower_id']} amt {match_amount}. Skipping match."
                        )
                        offer_idx += 1
                        continue

                else:
                    self.logger.error("CallMarket: Agent lookup failed during clearing.")
                    offer_idx += 1
                    continue

                # Advance indices if filled
                if offer['amount'] < 0.000001: # Float epsilon
                    offer_idx += 1
                if request['amount'] < 0.000001:
                    request_idx += 1
            else:
                # No overlap implies no further matches possible (since sorted)
                break

        # Calculate weighted average rate
        if total_volume > 0:
            self.last_clearing_rate = total_rate_volume / total_volume
        else:
            pass

        # Clear pending lists (Unfilled orders expire)
        self.pending_requests.clear()
        self.pending_offers.clear()

        return MarketClearingResultDTO(
            cleared_volume=total_volume,
            weighted_average_rate=self.last_clearing_rate,
            matched_loans=matched_loans
        )

    def get_market_rate(self) -> float:
        return self.last_clearing_rate

    def settle_matured_loans(self, tick: int) -> None:
        """
        Processes loans that have reached their maturity date.
        """
        matured_ids = []

        for loan_id, loan in self.active_loans.items():
            if tick >= loan['maturity_tick']:
                # Calculate Interest
                duration_ticks = loan['maturity_tick'] - loan['origination_tick']
                if duration_ticks <= 0:
                    duration_ticks = 1 # Safety

                time_fraction = duration_ticks / self.ticks_per_year
                interest_amount = loan['amount'] * loan['interest_rate'] * time_fraction

                total_repayment = loan['amount'] + interest_amount

                borrower = self.agent_registry.get_agent(loan['borrower_id'])
                lender = self.agent_registry.get_agent(loan['lender_id'])

                if borrower and lender:
                    memo = f"CallMarket Repayment {loan['borrower_id']}->{loan['lender_id']} Principal: {loan['amount']:.2f} Int: {interest_amount:.2f}"

                    tx = self.settlement_system.transfer(
                        debit_agent=borrower,
                        credit_agent=lender,
                        amount=total_repayment,
                        memo=memo,
                        tick=tick,
                        currency=DEFAULT_CURRENCY
                    )

                    if tx:
                        matured_ids.append(loan_id)
                    else:
                        self.logger.error(
                            f"CallMarket: Repayment FAILED for loan {loan_id}. Borrower {loan['borrower_id']} default?"
                        )
                        pass
                else:
                    self.logger.error(f"CallMarket: Agent lookup failed during repayment for loan {loan_id}")

        # Remove settled loans
        for mid in matured_ids:
            del self.active_loans[mid]
