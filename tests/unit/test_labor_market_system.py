import pytest
from unittest.mock import MagicMock
from modules.labor.system import LaborMarket
from modules.labor.api import JobOfferDTO, JobSeekerDTO
from modules.market.api import CanonicalOrderDTO
from modules.simulation.api import AgentID
from modules.common.enums import IndustryDomain

class TestLaborMarketSystem:
    @pytest.fixture
    def market(self):
        return LaborMarket()

    def test_post_job_offer(self, market):
        offer = JobOfferDTO(
            firm_id=AgentID(101),
            offer_wage=15.0,
            required_education=2,
            quantity=1.0,
            major=IndustryDomain.TECHNOLOGY
        )
        market.post_job_offer(offer)
        assert len(market._job_offers) == 1
        assert market._job_offers[0] == offer

    def test_post_job_seeker(self, market):
        seeker = JobSeekerDTO(
            household_id=AgentID(201),
            reservation_wage=12.0,
            education_level=3,
            quantity=1.0,
            major=IndustryDomain.TECHNOLOGY
        )
        market.post_job_seeker(seeker)
        assert len(market._job_seekers) == 1
        assert market._job_seekers[0] == seeker

    def test_match_market_perfect_match(self, market):
        offer = JobOfferDTO(
            firm_id=AgentID(101),
            offer_wage=20.0,
            required_education=2,
            major=IndustryDomain.TECHNOLOGY
        )
        seeker = JobSeekerDTO(
            household_id=AgentID(201),
            reservation_wage=15.0,
            education_level=2,
            major=IndustryDomain.TECHNOLOGY
        )
        market.post_job_offer(offer)
        market.post_job_seeker(seeker)

        results = market.match_market(current_tick=1)

        assert len(results) == 1
        match = results[0]
        assert match.employer_id == AgentID(101)
        assert match.employee_id == AgentID(201)
        assert match.matched_wage == 17.5 # Nash Bargaining: (20 + 15) / 2
        assert match.major_compatibility == "PERFECT"

        # Check queues cleared
        assert len(market._job_offers) == 0
        assert len(market._job_seekers) == 0

    def test_match_market_mismatch_major(self, market):
        offer = JobOfferDTO(
            firm_id=AgentID(101),
            offer_wage=20.0,
            required_education=2,
            major=IndustryDomain.TECHNOLOGY
        )
        seeker = JobSeekerDTO(
            household_id=AgentID(201),
            reservation_wage=15.0,
            education_level=2,
            major=IndustryDomain.FOOD_PROD
        )
        market.post_job_offer(offer)
        market.post_job_seeker(seeker)

        results = market.match_market(current_tick=1)

        # Should match but with lower priority/score if no better option
        # Multiplier 0.8. Base 20/15 = 1.33. Final = 1.33 * 0.8 = 1.06 > 1.0. Match.
        assert len(results) == 1
        match = results[0]
        assert match.major_compatibility == "MISMATCH"

    def test_match_market_wage_too_low(self, market):
        offer = JobOfferDTO(
            firm_id=AgentID(101),
            offer_wage=10.0,
            required_education=2,
            major=IndustryDomain.TECHNOLOGY
        )
        seeker = JobSeekerDTO(
            household_id=AgentID(201),
            reservation_wage=15.0,
            education_level=2,
            major=IndustryDomain.TECHNOLOGY
        )
        market.post_job_offer(offer)
        market.post_job_seeker(seeker)

        results = market.match_market(current_tick=1)

        assert len(results) == 0

    def test_place_order_adapter(self, market):
        buy_order = CanonicalOrderDTO(
            agent_id=101,
            side="BUY",
            item_id="labor",
            quantity=1.0,
            price_pennies=2000,
            market_id="labor",
            metadata={"major": "TECHNOLOGY", "required_education": 2}
        )
        sell_order = CanonicalOrderDTO(
            agent_id=201,
            side="SELL",
            item_id="labor",
            quantity=1.0,
            price_pennies=1500,
            market_id="labor",
            brand_info={"major": "TECHNOLOGY", "education_level": 2} # brand_info used by Household
        )

        market.place_order(buy_order, 1)
        market.place_order(sell_order, 1)

        assert len(market._job_offers) == 1
        assert len(market._job_seekers) == 1
        assert market._job_offers[0].offer_wage == 20.0
        assert market._job_seekers[0].reservation_wage == 15.0

        txs = market.match_orders(1)
        assert len(txs) == 1
        assert txs[0].transaction_type == "HIRE"
        assert txs[0].total_pennies == 1750 # Nash Bargaining: (2000 + 1500) / 2

    def test_place_order_backward_compatibility(self, market):
        # CanonicalOrderDTO without metadata (Legacy)
        buy_order = CanonicalOrderDTO(
            agent_id=101,
            side="BUY",
            item_id="labor",
            quantity=1.0,
            price_pennies=2000,
            market_id="labor"
            # No metadata
        )
        sell_order = CanonicalOrderDTO(
            agent_id=201,
            side="SELL",
            item_id="labor",
            quantity=1.0,
            price_pennies=1500,
            market_id="labor"
            # No brand_info
        )

        market.place_order(buy_order, 1)
        market.place_order(sell_order, 1)

        assert len(market._job_offers) == 1
        assert len(market._job_seekers) == 1

        # Verify defaults
        assert market._job_offers[0].major == IndustryDomain.GENERAL
        assert market._job_offers[0].required_education == 0
        assert market._job_seekers[0].major == IndustryDomain.GENERAL
        assert market._job_seekers[0].education_level == 0

        txs = market.match_orders(1)
        assert len(txs) == 1
