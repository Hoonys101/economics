import pytest
from unittest.mock import MagicMock, PropertyMock
from modules.labor.system import LaborMarket
from modules.labor.api import JobOfferDTO, JobSeekerDTO
from modules.common.enums import IndustryDomain
from modules.household.engines.budget import BudgetEngine, DESPERATION_THRESHOLD_TICKS, DESPERATION_WAGE_DECAY, SHADOW_WAGE_UNEMPLOYED_DECAY
from modules.household.dtos import EconStateDTO
from simulation.firms import Firm
from simulation.models import Order

class TestLaborThaw:

    # --- 1. Desperation Wage Decay Tests ---

    def test_desperation_wage_decay(self):
        engine = BudgetEngine()
        state = MagicMock(spec=EconStateDTO)
        state.is_employed = False
        state.shadow_reservation_wage_pennies = 1000
        state.last_fired_tick = 1 # Tick 1
        state.market_wage_history = []
        state.current_wage_pennies = 0
        state.expected_wage_pennies = 1000

        config = MagicMock()
        config.household_min_wage_demand = 0 # Fix: Mock config value

        # Case 1: Short unemployment (Normal Decay)
        current_tick = 5
        # unemployment_duration = 5 - 1 = 4. < 20.
        # decay = 1.0 - 0.02 = 0.98
        engine._update_shadow_wage(state, MagicMock(), config, current_tick)

        expected_wage = int(1000 * (1.0 - SHADOW_WAGE_UNEMPLOYED_DECAY)) # 980
        assert state.shadow_reservation_wage_pennies == expected_wage

        # Case 2: Long unemployment (Desperation Decay)
        state.shadow_reservation_wage_pennies = 1000
        current_tick = 30
        # unemployment_duration = 30 - 1 = 29. > 20.
        # decay = 0.95
        engine._update_shadow_wage(state, MagicMock(), config, current_tick)

        expected_desperate_wage = int(1000 * DESPERATION_WAGE_DECAY) # 950
        assert state.shadow_reservation_wage_pennies == expected_desperate_wage

        # Verify Desperation is stronger than Normal
        assert expected_desperate_wage < expected_wage

    # --- 2. Talent Signal & Matching Tests ---

    def test_talent_signal_boosts_score(self):
        market = LaborMarket()

        offer = JobOfferDTO(
            firm_id=1,
            offer_wage_pennies=1000,
            major=IndustryDomain.GENERAL,
            quantity=1
        )
        market.post_job_offer(offer)

        # Seeker 1: Normal Talent (1.0)
        seeker1 = JobSeekerDTO(
            household_id=101,
            reservation_wage_pennies=1000,
            education_level=0, # Fix: Added required arg
            major=IndustryDomain.GENERAL,
            talent_score=1.0
        )
        market.post_job_seeker(seeker1)

        # Seeker 2: High Talent (1.5)
        seeker2 = JobSeekerDTO(
            household_id=102,
            reservation_wage_pennies=1000,
            education_level=0, # Fix: Added required arg
            major=IndustryDomain.GENERAL,
            talent_score=1.5
        )
        market.post_job_seeker(seeker2)

        matches = market.match_market(current_tick=1)

        assert len(matches) == 1
        # Seeker 2 should win due to higher score
        # Seeker 1 score: 1.0 (base) * 1.0 (talent) = 1.0
        # Seeker 2 score: 1.0 (base) * (1.0 + (1.5-1.0)*0.5) = 1.25
        assert matches[0].employee_id == 102
        assert matches[0].match_score > 1.0

    def test_relaxed_wage_filter(self):
        market = LaborMarket()

        # Offer: 950 pennies
        offer = JobOfferDTO(
            firm_id=1,
            offer_wage_pennies=950,
            major=IndustryDomain.GENERAL,
            quantity=1
        )
        market.post_job_offer(offer)

        # Seeker: Reservation 1000 pennies
        # Ratio = 0.95. Previous logic would reject (<1.0). New logic accepts (>=0.9).
        seeker = JobSeekerDTO(
            household_id=101,
            reservation_wage_pennies=1000,
            education_level=0, # Fix: Added required arg
            major=IndustryDomain.GENERAL,
            talent_score=1.0
        )
        market.post_job_seeker(seeker)

        matches = market.match_market(current_tick=1)

        assert len(matches) == 1
        assert matches[0].employee_id == 101
        # Matched wage should be offer wage (950) since surplus is negative?
        # Logic: if surplus > 0: ... else: best_wage_pennies = offer.offer_wage_pennies
        assert matches[0].matched_wage_pennies == 950

    # --- 3. Liquidity Pre-flight Check Tests ---

    def test_firm_liquidity_preflight_check(self):
        # Fix imports
        from modules.firm.api import HRIntentDTO, HRContextDTO
        from modules.simulation.api import AgentID

        firm = MagicMock(spec=Firm)
        firm.id = 1
        firm.financial_component = MagicMock()
        firm.logger = MagicMock()

        # Bind the method
        firm._generate_hr_orders = Firm._generate_hr_orders.__get__(firm, Firm)

        intent = HRIntentDTO(hiring_target=1, fire_employee_ids=[], wage_updates={})
        context = HRContextDTO(
            firm_id=1, tick=1, budget_pennies=10000,
            market_snapshot=MagicMock(), available_cash_pennies=0, is_solvent=True,
            current_employees=[], current_headcount=0, employee_wages={}, employee_skills={},
            target_workforce_count=1, labor_market_avg_wage=1000, marginal_labor_productivity=1.0,
            happiness_avg=0.0, profit_history=[], min_employees=1, max_employees=100, severance_pay_weeks=2,
            specialization="FOOD", major=IndustryDomain.GENERAL,
            hires_prev_tick=0, target_hires_prev_tick=0, wage_offer_prev_tick=0
        )

        # Case 1: Sufficient Cash
        firm.financial_component.get_balance.return_value = 5000 # Enough for ~1000 wage
        orders = firm._generate_hr_orders(intent, context)
        assert len(orders) == 1
        assert orders[0].metadata['is_liquidity_verified'] == True

        # Case 2: Insufficient Cash
        firm.financial_component.get_balance.return_value = 500 # Less than wage ~1000
        # Wage offer calculation might vary, but ~1000 base.
        # Logic: offered_wage = int(base_wage * (1 + wage_premium))
        # base_wage=1000. offered_wage >= 1000.
        # projected_cost = 1000 * 1 = 1000.
        # 500 < 1000. Should block.
        orders = firm._generate_hr_orders(intent, context)
        assert len(orders) == 0
