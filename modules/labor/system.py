from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
from modules.labor.api import ILaborMarket, JobOfferDTO, JobSeekerDTO, LaborMarketMatchResultDTO
from modules.market.api import CanonicalOrderDTO, OrderTelemetrySchema
from simulation.models import Transaction
from simulation.interfaces.market_interface import IMarket
from modules.simulation.api import AgentID

logger = logging.getLogger(__name__)

class LaborMarket(ILaborMarket, IMarket):
    """
    Implementation of the Labor Market with Major-Matching logic.
    """
    def __init__(self, market_id: str = "labor"):
        self.id = market_id
        self._job_offers: List[JobOfferDTO] = []
        self._job_seekers: List[JobSeekerDTO] = []
        self._matched_transactions: List[Transaction] = []

        # IMarket compatibility
        self._buy_orders_cache: Dict[str, List[CanonicalOrderDTO]] = {}
        self._sell_orders_cache: Dict[str, List[CanonicalOrderDTO]] = {}

    def post_job_offer(self, offer: JobOfferDTO) -> None:
        self._job_offers.append(offer)

    def post_job_seeker(self, seeker: JobSeekerDTO) -> None:
        self._job_seekers.append(seeker)

    def match_market(self, current_tick: int) -> List[LaborMarketMatchResultDTO]:
        matches: List[LaborMarketMatchResultDTO] = []

        # Sort offers by wage descending (High paying jobs pick first)
        sorted_offers = sorted(self._job_offers, key=lambda x: x.offer_wage, reverse=True)

        # Bucket seekers by Major for Performance Optimization (O(N*M) -> O(N*K) where K is subset)
        seekers_by_major: Dict[str, List[JobSeekerDTO]] = {}
        for seeker in self._job_seekers:
            major = seeker.major
            if major not in seekers_by_major:
                seekers_by_major[major] = []
            seekers_by_major[major].append(seeker)

        # Also maintain a set of matched IDs to prevent double-booking
        matched_seeker_ids = set()

        for offer in sorted_offers:
            # Determine relevant buckets to search
            # Priority 1: Same Major
            # Priority 2: GENERAL Major (or if offer is GENERAL)
            # Priority 3: All others (if desperate/allowed, but for perf we limit)

            search_buckets = [offer.major]
            if "GENERAL" not in search_buckets:
                search_buckets.append("GENERAL")

            # Add all other buckets for broader search if needed, but penalize?
            # For strict perf, we might only check primary buckets.
            # Let's iterate all buckets but order them.
            all_majors = list(seekers_by_major.keys())
            remaining = [m for m in all_majors if m not in search_buckets]
            search_buckets.extend(remaining)

            best_candidate = None
            best_score = -1.0
            best_wage = 0.0
            best_compatibility = "MISMATCH"

            for major_key in search_buckets:
                if major_key not in seekers_by_major:
                    continue

                candidates = seekers_by_major[major_key]

                for seeker in candidates:
                    if seeker.household_id in matched_seeker_ids:
                        continue

                    # 1. Base Score (Wage vs Reservation)
                    if seeker.reservation_wage <= 0:
                        base_score = 1.0
                    else:
                        base_score = offer.offer_wage / seeker.reservation_wage

                    # Filter: Must meet reservation wage
                    if base_score < 1.0:
                        continue

                    # 2. Major Matching
                    major_multiplier = 1.0
                    compatibility = "MISMATCH"

                    if offer.major == seeker.major:
                        major_multiplier = 1.2
                        compatibility = "PERFECT"
                    elif seeker.secondary_majors and offer.major in seeker.secondary_majors:
                        major_multiplier = 1.1
                        compatibility = "PARTIAL"
                    elif offer.major == "GENERAL" or seeker.major == "GENERAL":
                        major_multiplier = 1.0
                        compatibility = "PARTIAL"
                    else:
                        major_multiplier = 0.8 # Penalty for mismatch

                    # 3. Education Matching
                    edu_multiplier = 1.0
                    if seeker.education_level < offer.required_education:
                        edu_multiplier = 0.5 # Severe penalty
                    elif seeker.education_level > offer.required_education:
                        # Small bonus for over-qualification? Or diminishing return?
                        # Let's say slight bonus.
                        edu_multiplier = 1.05

                    final_score = base_score * major_multiplier * edu_multiplier

                    if final_score > best_score:
                        best_score = final_score
                        best_candidate = seeker
                        # Wage determination: usually offer wage, or mid-point?
                        # For simplicity, use offer wage.
                        best_wage = offer.offer_wage
                        best_compatibility = compatibility

            if best_candidate:
                matches.append(LaborMarketMatchResultDTO(
                    employer_id=offer.firm_id,
                    employee_id=best_candidate.household_id,
                    base_wage=offer.offer_wage,
                    matched_wage=best_wage,
                    match_score=best_score,
                    major_compatibility=best_compatibility
                ))
                matched_seeker_ids.add(best_candidate.household_id)

        # Clear queues after matching
        self._job_offers.clear()
        self._job_seekers.clear()
        self._buy_orders_cache.clear()
        self._sell_orders_cache.clear()

        return matches

    # --- IMarket Implementation ---

    @property
    def buy_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        # Map JobOffers to Orders on demand or maintain cache
        # If cache empty and offers exist, rebuild?
        # For now, return empty or implement mapping if needed by UI/Analytics
        return self._buy_orders_cache

    @property
    def sell_orders(self) -> Dict[str, List[CanonicalOrderDTO]]:
        return self._sell_orders_cache

    @property
    def matched_transactions(self) -> List[Transaction]:
        return self._matched_transactions

    def get_daily_avg_price(self) -> float:
        # Calculate from matched transactions
        total = sum(tx.price * tx.quantity for tx in self._matched_transactions)
        volume = sum(tx.quantity for tx in self._matched_transactions)
        return total / volume if volume > 0 else 0.0

    def get_daily_volume(self) -> float:
        return sum(tx.quantity for tx in self._matched_transactions)

    def get_price(self, item_id: str) -> float:
        return self.get_daily_avg_price()

    def cancel_orders(self, agent_id: str) -> None:
        # Remove offers/seekers for agent
        # Assuming AgentID is int, but str passed here. Convert?
        try:
            aid = int(agent_id)
            self._job_offers = [o for o in self._job_offers if int(o.firm_id) != aid]
            self._job_seekers = [s for s in self._job_seekers if int(s.household_id) != aid]
        except ValueError:
            pass

    def place_order(self, order_dto: CanonicalOrderDTO, current_time: int) -> List[Transaction]:
        """
        Adapter: CanonicalOrderDTO -> JobOffer/JobSeeker
        """
        # Store in cache for IMarket visibility
        if order_dto.side == "BUY":
            if "labor" not in self._buy_orders_cache: self._buy_orders_cache["labor"] = []
            self._buy_orders_cache["labor"].append(order_dto)

            # Convert to JobOffer
            metadata = order_dto.metadata or {}
            offer = JobOfferDTO(
                firm_id=AgentID(int(order_dto.agent_id)),
                offer_wage=order_dto.price_pennies / 100.0,
                required_education=metadata.get("required_education", 0),
                quantity=order_dto.quantity,
                major=metadata.get("major", "GENERAL")
            )
            self.post_job_offer(offer)

        elif order_dto.side == "SELL":
            if "labor" not in self._sell_orders_cache: self._sell_orders_cache["labor"] = []
            self._sell_orders_cache["labor"].append(order_dto)

            # Convert to JobSeeker
            metadata = order_dto.brand_info or {} # Household uses brand_info for metadata
            seeker = JobSeekerDTO(
                household_id=AgentID(int(order_dto.agent_id)),
                reservation_wage=order_dto.price_pennies / 100.0,
                education_level=metadata.get("education_level", 0),
                quantity=order_dto.quantity,
                major=metadata.get("major", "GENERAL")
            )
            self.post_job_seeker(seeker)

        return [] # No immediate transactions

    def match_orders(self, current_time: int) -> List[Transaction]:
        """
        Executes matching and returns Transactions (HIRE type).
        """
        results = self.match_market(current_time)
        transactions = []

        for res in results:
            # Create HIRE transaction
            tx = Transaction(
                buyer_id=res.employer_id,
                seller_id=res.employee_id,
                item_id="labor",
                quantity=1.0,
                price=res.matched_wage,
                market_id=self.id,
                transaction_type="HIRE",
                time=current_time,
                total_pennies=int(res.matched_wage * 100),
                metadata={
                    "match_score": res.match_score,
                    "major_compatibility": res.major_compatibility,
                    "base_wage": res.base_wage
                }
            )
            transactions.append(tx)

        self._matched_transactions.extend(transactions)
        return transactions

    def clear_orders(self) -> None:
        self._job_offers.clear()
        self._job_seekers.clear()
        self._buy_orders_cache.clear()
        self._sell_orders_cache.clear()

    def get_telemetry_snapshot(self) -> List[OrderTelemetrySchema]:
        telemetry = []
        for lst in self._buy_orders_cache.values():
            for o in lst:
                telemetry.append(OrderTelemetrySchema.from_canonical(o))
        for lst in self._sell_orders_cache.values():
            for o in lst:
                telemetry.append(OrderTelemetrySchema.from_canonical(o))
        return telemetry

    def get_total_demand(self) -> float:
        """Returns total demand (job offers)."""
        return sum(offer.quantity for offer in self._job_offers)

    def get_total_supply(self) -> float:
        """Returns total supply (job seekers)."""
        return sum(seeker.quantity for seeker in self._job_seekers)
