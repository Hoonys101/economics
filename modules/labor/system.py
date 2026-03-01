from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
from modules.labor.api import ILaborMarket, JobOfferDTO, JobSeekerDTO, LaborMarketMatchResultDTO, LaborConfigDTO
from modules.market.api import CanonicalOrderDTO, OrderTelemetrySchema, LaborMarketConfigDTO
from simulation.models import Transaction
from simulation.interfaces.market_interface import IMarket
from modules.simulation.api import AgentID
from modules.common.enums import IndustryDomain

logger = logging.getLogger(__name__)

class LaborMarket(ILaborMarket, IMarket):
    """
    Implementation of the Labor Market with Major-Matching logic.
    """
    def __init__(self, market_id: str = "labor", config_dto: Optional[LaborMarketConfigDTO] = None):
        self.id = market_id
        self._job_offers: List[JobOfferDTO] = []
        self._job_seekers: List[JobSeekerDTO] = []
        self._matched_transactions: List[Transaction] = []
        self.config = config_dto or LaborMarketConfigDTO()

        # IMarket compatibility
        self._buy_orders_cache: Dict[str, List[CanonicalOrderDTO]] = {}
        self._sell_orders_cache: Dict[str, List[CanonicalOrderDTO]] = {}

    def configure(self, config: LaborConfigDTO) -> None:
        """
        Injects configuration into the Labor Market.
        """
        # Logic to apply config if needed
        pass

    def post_job_offer(self, offer: JobOfferDTO) -> None:
        self._job_offers.append(offer)

    def post_job_seeker(self, seeker: JobSeekerDTO) -> None:
        self._job_seekers.append(seeker)

    def match_market(self, current_tick: int) -> List[LaborMarketMatchResultDTO]:
        matches: List[LaborMarketMatchResultDTO] = []

        # TD-WAVE3-MATCH-REWRITE: Delegate to stateless engine
        context = JobMatchContextDTO(
            tick=current_tick,
            available_seekers=self._job_seekers,
            available_offers=self._job_offers,
            market_panic_index=0.0 # Could be passed from somewhere if available
        )

        # We need to pass the config to execute_labor_matching so it can do the multipliers
        result = execute_labor_matching(context, self.config)

        # Convert matched_pairs to LaborMarketMatchResultDTO format for backward compatibility
        for seeker_id, firm_id in result.matched_pairs.items():
            wage = result.agreed_wages_pennies[seeker_id]

            # Resolve the exact offer that matched.
            # To avoid taking just the first one arbitrarily, we look at unmatched_offers from result
            # meaning the ones that were NOT matched. This still means we need to know the original offer.
            # However, since the engine removed the matched offer from unmatched_offers,
            # we can identify it by looking at original offers minus unmatched offers.
            original_offers_for_firm = [o for o in self._job_offers if o.firm_id == firm_id]
            unmatched_for_firm = [o for o in result.unmatched_offers if o.firm_id == firm_id]

            # A matched offer is one that is in original but not in unmatched
            # To handle multiple identical offers, we can just take the first one that is missing from unmatched
            # Or simpler: base_wage is the highest offer for this firm that was matched.
            # For simplicity, since the engine sorted by highest wage, the matched offer is the highest one that isn't in unmatched_for_firm
            # but wait, `result.unmatched_offers` contains actual instances if `.copy()` was shallow.
            matched_offers = [o for o in original_offers_for_firm if o not in unmatched_for_firm]
            offer = matched_offers[0] if matched_offers else original_offers_for_firm[0]

            base_wage = offer.offer_wage_pennies

            # Reconstruct original reservation wage to calculate true surplus
            seeker = next((s for s in self._job_seekers if s.household_id == seeker_id), None)
            res_wage = seeker.reservation_wage_pennies if seeker else wage
            surplus = base_wage - res_wage

            # Calculate match score & compatibility dynamically just for the report/telemetry
            # To stay stateless, we can just recalculate the simplified multiplier
            req_talent = getattr(offer, 'min_match_score', 0.0)
            seeker_talent = getattr(seeker, 'talent_score', 1.0) if seeker else 1.0
            score = 1.0 + (seeker_talent - 1.0) * 0.5

            offer_major = getattr(offer, 'major', IndustryDomain.GENERAL)
            seeker_major = getattr(seeker, 'major', IndustryDomain.GENERAL)
            compat = "PERFECT" if offer_major == seeker_major else "MISMATCH"
            if offer_major == IndustryDomain.GENERAL or seeker_major == IndustryDomain.GENERAL:
                compat = "PARTIAL"

            matches.append(LaborMarketMatchResultDTO(
                employer_id=firm_id,
                employee_id=seeker_id,
                base_wage_pennies=base_wage,
                matched_wage_pennies=wage,
                match_score=score,
                major_compatibility=compat,
                surplus_pennies=surplus,
                bargaining_power=0.5
            ))

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

            # Use DTO major if valid, otherwise fallback to metadata
            major_enum = order_dto.major if order_dto.major != IndustryDomain.GENERAL else None

            if not major_enum:
                major_str = metadata.get("major", "GENERAL")
                try:
                    major_enum = IndustryDomain(major_str)
                except ValueError:
                    major_enum = IndustryDomain.GENERAL

            offer = JobOfferDTO(
                firm_id=AgentID(int(order_dto.agent_id)),
                offer_wage_pennies=int(order_dto.price_pennies),
                required_education=metadata.get("required_education", 0),
                quantity=order_dto.quantity,
                major=major_enum,
                is_liquidity_verified=metadata.get("is_liquidity_verified", False)
            )
            self.post_job_offer(offer)

        elif order_dto.side == "SELL":
            if "labor" not in self._sell_orders_cache: self._sell_orders_cache["labor"] = []
            self._sell_orders_cache["labor"].append(order_dto)

            # Convert to JobSeeker
            metadata = order_dto.metadata or order_dto.brand_info or {} # Household uses brand_info for metadata, but metadata is also checked

            # Use DTO major if valid, otherwise fallback to metadata
            major_enum = order_dto.major if order_dto.major != IndustryDomain.GENERAL else None

            if not major_enum:
                major_str = metadata.get("major", "GENERAL")
                try:
                    major_enum = IndustryDomain(major_str)
                except ValueError:
                    major_enum = IndustryDomain.GENERAL

            seeker = JobSeekerDTO(
                household_id=AgentID(int(order_dto.agent_id)),
                reservation_wage_pennies=int(order_dto.price_pennies),
                education_level=metadata.get("education_level", 0),
                quantity=order_dto.quantity,
                major=major_enum,
                talent_score=float(metadata.get("talent_score", 1.0))
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
            # MIGRATION: matched_wage is now derived from matched_wage_pennies
            matched_wage = float(res.matched_wage_pennies) / 100.0

            tx = Transaction(
                buyer_id=res.employer_id,
                seller_id=res.employee_id,
                item_id="labor",
                quantity=1.0,
                price=matched_wage,
                market_id=self.id,
                transaction_type="HIRE",
                time=current_time,
                total_pennies=res.matched_wage_pennies,
                metadata={
                    "match_score": res.match_score,
                    "major_compatibility": res.major_compatibility,
                    "base_wage": float(res.base_wage_pennies) / 100.0,
                    "surplus": float(res.surplus_pennies) / 100.0,
                    "bargaining_power": res.bargaining_power
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

# TD-WAVE3-MATCH-REWRITE: Labor Market Bargaining
from simulation.dtos.api import JobMatchContextDTO, LaborMatchingResultDTO

def execute_labor_matching(context: JobMatchContextDTO, config=None) -> LaborMatchingResultDTO:
    """
    Stateless matching engine.
    """
    # SORT available_seekers BY hidden_talent DESC (using talent_score from JobSeekerDTO)
    # SORT available_offers BY wage_offered_pennies DESC
    available_seekers = sorted(context.available_seekers, key=lambda s: getattr(s, 'talent_score', 1.0), reverse=True)
    available_offers = sorted(context.available_offers, key=lambda o: getattr(o, 'offer_wage_pennies', 0), reverse=True)

    matched_pairs = {}
    agreed_wages_pennies = {}

    unmatched_offers = available_offers.copy()
    unmatched_seekers = []

    for seeker in available_seekers:
        matched = False
        best_offer = None
        best_score = -1.0
        best_wage_pennies = 0
        best_compatibility = "MISMATCH"

        for offer in unmatched_offers:
            reservation_wage = getattr(seeker, 'reservation_wage_pennies', 0)
            offer_wage = getattr(offer, 'offer_wage_pennies', 0)

            # Base logic relaxed to 0.9 for thaw
            if reservation_wage <= 0:
                base_score = 1.0
            else:
                base_score = offer_wage / reservation_wage

            if base_score < 0.9:
                continue

            required_talent = getattr(offer, 'min_match_score', 0.0)
            seeker_talent = getattr(seeker, 'talent_score', 1.0)

            # Talent multiplier
            talent_multiplier = 1.0 + (seeker_talent - 1.0) * 0.5

            # Major matching
            major_multiplier = 1.0
            compatibility = "MISMATCH"

            mult_perfect = 1.2
            mult_partial = 1.0
            mult_mismatch = 0.8
            mult_general = 1.0

            if config and hasattr(config, 'compatibility'):
                compat_config = config.compatibility
                mult_perfect = compat_config.get('PERFECT', mult_perfect)
                mult_partial = compat_config.get('PARTIAL', mult_partial)
                mult_mismatch = compat_config.get('MISMATCH', mult_mismatch)
                mult_general = compat_config.get('GENERAL_PENALTY', mult_general)

            offer_major = getattr(offer, 'major', IndustryDomain.GENERAL)
            seeker_major = getattr(seeker, 'major', IndustryDomain.GENERAL)
            secondary_majors = getattr(seeker, 'secondary_majors', [])

            if offer_major == seeker_major:
                major_multiplier = mult_perfect
                compatibility = "PERFECT"
            elif secondary_majors and offer_major in secondary_majors:
                major_multiplier = mult_partial
                compatibility = "PARTIAL"
            elif offer_major == IndustryDomain.GENERAL or seeker_major == IndustryDomain.GENERAL:
                major_multiplier = mult_general
                compatibility = "PARTIAL"
            else:
                major_multiplier = mult_mismatch

            # Education matching
            edu_multiplier = 1.0
            req_edu = getattr(offer, 'required_education', 0)
            seek_edu = getattr(seeker, 'education_level', 0)
            if seek_edu < req_edu:
                edu_multiplier = 0.5
            elif seek_edu > req_edu:
                edu_multiplier = 1.05

            final_score = base_score * major_multiplier * edu_multiplier * talent_multiplier

            if final_score > best_score and seeker_talent >= required_talent:
                best_score = final_score
                best_offer = offer
                best_compatibility = compatibility

                surplus = offer_wage - reservation_wage
                bargaining_power = 0.5

                if surplus > 0:
                    best_wage_pennies = int(reservation_wage + (surplus * bargaining_power))
                else:
                    best_wage_pennies = offer_wage

        if best_offer:
            # DTO Type compliance: matched_pairs is Dict[AgentID, AgentID]
            matched_pairs[seeker.household_id] = best_offer.firm_id

            # Since matched_pairs only holds the firm_id, we need to pass the metadata
            # We can either expand LaborMatchingResultDTO or return it differently
            # For now, let's keep it pure to the DTO and let the orchestrator re-calculate
            # or we can just assume match_score 1.0/PERFECT as an initial naive state
            # if we can't change DTO or we pass it via agreed_wages if we really needed.
            # We will just comply with the strict DTO typing for matched_pairs

            agreed_wages_pennies[seeker.household_id] = best_wage_pennies
            unmatched_offers.remove(best_offer)
            matched = True

        if not matched:
            unmatched_seekers.append(seeker.household_id)

    return LaborMatchingResultDTO(
        matched_pairs=matched_pairs,
        agreed_wages_pennies=agreed_wages_pennies,
        unmatched_seekers=unmatched_seekers,
        unmatched_offers=unmatched_offers
    )
