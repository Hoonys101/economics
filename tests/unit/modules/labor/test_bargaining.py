import unittest
from unittest.mock import MagicMock
from modules.labor.system import LaborMarket
from modules.labor.api import JobOfferDTO, JobSeekerDTO
from simulation.components.engines.hr_engine import HREngine
from modules.firm.api import HRContextDTO, AgentID, MarketSnapshotDTO

class TestBargainingAndAdaptiveLearning(unittest.TestCase):

    def test_nash_bargaining_surplus_sharing(self):
        # Setup Market
        market = LaborMarket()

        # WTP (Firm) = 2000 (20.00), WTA (Worker) = 1000 (10.00)
        # Surplus = 10.00
        # Split = 0.5 (Default) -> Price = 10.00 + 5.00 = 15.00

        offer = JobOfferDTO(
            firm_id=AgentID(1),
            offer_wage_pennies=2000,
            required_education=0,
            quantity=1.0,
            major="GENERAL"
        )

        seeker = JobSeekerDTO(
            household_id=AgentID(101),
            reservation_wage_pennies=1000,
            education_level=0,
            quantity=1.0,
            major="GENERAL"
        )

        market.post_job_offer(offer)
        market.post_job_seeker(seeker)

        matches = market.match_market(current_tick=1)

        self.assertEqual(len(matches), 1)
        match = matches[0]

        self.assertEqual(match.employer_id, 1)
        self.assertEqual(match.employee_id, 101)
        self.assertAlmostEqual(match.base_wage_pennies, 2000)
        self.assertAlmostEqual(match.matched_wage_pennies, 1500) # (10 + 20) / 2
        self.assertAlmostEqual(match.surplus_pennies, 1000)
        self.assertAlmostEqual(match.bargaining_power, 0.5)

    def test_firm_adaptive_learning_wage_increase(self):
        # Scenario: Firm failed to hire in previous tick
        # target_hires = 5, actual_hires = 0
        # TD-Error > 0 -> Increase Wage

        engine = HREngine()

        # Mock Context
        context = MagicMock(spec=HRContextDTO)
        context.target_workforce_count = 10
        context.current_headcount = 5
        context.budget_pennies = 1000000
        context.labor_market_avg_wage = 1000 # 10.00
        context.profit_history = [10000]
        context.employee_wages = {}
        context.current_employees = []
        context.min_employees = 1
        context.max_employees = 100
        context.severance_pay_weeks = 2

        # Adaptive History
        context.target_hires_prev_tick = 5
        context.hires_prev_tick = 0 # Failed!
        context.wage_offer_prev_tick = 1000 # 10.00

        intent = engine.decide_workforce(context)

        # Expect wage > 1000 (adaptive premium applied)
        # Profit premium: 10000/(1000*10) = 1.0 -> 0.1 (10%)
        # Base increase = 1000 * 1.1 = 1100.

        # Adaptive:
        # hiring_deficit = 5.
        # adaptive_premium = 0.1 * (5/5) = 0.1 (10%).
        # total_premium = 0.1 + 0.1 = 0.2 (20%).
        # Target Wage = 1000 * 1.2 = 1200.

        self.assertGreater(intent.hiring_wage_offer, 1100)
        self.assertEqual(intent.hiring_wage_offer, 1200)

    def test_firm_adaptive_learning_wage_decrease(self):
        # Scenario: Firm hired everyone easily
        # target_hires = 5, actual_hires = 5
        # TD-Error <= 0 -> Decrease/Hold

        engine = HREngine()

        context = MagicMock(spec=HRContextDTO)
        context.target_workforce_count = 10
        context.current_headcount = 5
        context.budget_pennies = 1000000
        context.labor_market_avg_wage = 1000
        context.profit_history = [10000] # Premium 0.1
        context.employee_wages = {}
        context.current_employees = []
        context.min_employees = 1
        context.max_employees = 100
        context.severance_pay_weeks = 2

        # Adaptive History
        context.target_hires_prev_tick = 5
        context.hires_prev_tick = 5 # Success!
        context.wage_offer_prev_tick = 1200

        intent = engine.decide_workforce(context)

        # Base premium 0.1.
        # Adaptive premium:
        # hiring_deficit = 0.
        # actual_hires > 0 -> -0.01 (-1%).
        # total_premium = 0.1 - 0.01 = 0.09.

        # Anchor: base_wage (1000).
        # (Last offer > base, but deficit <= 0, so anchor reset to base)

        # Target = 1000 * 1.09 = 1090.

        self.assertEqual(intent.hiring_wage_offer, 1090)
