import unittest
from unittest.mock import MagicMock
from simulation.firms import Firm
from simulation.core_agents import Household
from modules.hr.service import HRService
from modules.finance.service import TaxService
from modules.system.registry import AgentRegistry
from simulation.dtos.config_dtos import FirmConfigDTO

class TestLiquidationServices(unittest.TestCase):
    def setUp(self):
        self.hr_service = HRService()
        self.agent_registry = AgentRegistry()
        self.tax_service = TaxService(self.agent_registry)

        # Mock Config
        self.config = MagicMock(spec=FirmConfigDTO)
        self.config.ticks_per_year = 365
        self.config.severance_pay_weeks = 2.0
        self.config.corporate_tax_rate = 0.2

        # Mock Firm
        self.firm = MagicMock(spec=Firm)
        self.firm.config = self.config
        self.firm.hr_state = MagicMock()
        self.firm.finance_state = MagicMock()
        self.firm.id = 1
        self.firm.finance_state.current_profit = 0.0

    def test_hr_service_unpaid_wages(self):
        current_tick = 1000
        # Wage cutoff = 1000 - 91 = 909

        # Employee 1: Unpaid wages 500 (tick 950 - OK)
        # Employee 2: Unpaid wages 500 (tick 800 - Too Old)

        self.firm.hr_state.unpaid_wages = {
            101: [(950, 500.0)],
            102: [(800, 500.0)]
        }
        self.firm.hr_state.employees = []
        self.firm.hr_state.employee_wages = {}

        claims = self.hr_service.calculate_liquidation_employee_claims(self.firm, current_tick)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].creditor_id, 101)
        self.assertEqual(claims[0].amount, 500.0)
        self.assertEqual(claims[0].tier, 1)

    def test_hr_service_severance(self):
        current_tick = 2000

        # Employee: 2 years tenure
        # Start tick = 2000 - (365 * 2) = 1270
        emp = MagicMock()
        emp.id = 101
        emp._econ_state.employment_start_tick = 1270

        self.firm.hr_state.employees = [emp]
        self.firm.hr_state.employee_wages = {101: 100.0}
        self.firm.hr_state.unpaid_wages = {}

        # Severance = 2 yrs * 2 weeks/yr * 7.019 ticks/week * 100 wage
        # ticks_per_week = 365/52 = 7.01923
        # 2 * 2 * 7.019 * 100 = 2807.69

        claims = self.hr_service.calculate_liquidation_employee_claims(self.firm, current_tick)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].creditor_id, 101)
        self.assertAlmostEqual(claims[0].amount, 2807.69, delta=1.0)

    def test_tax_service(self):
        self.firm.finance_state.current_profit = 1000.0

        # Mock Registry to return Government
        gov_agent = MagicMock()
        gov_agent.id = "gov_real_id"
        self.agent_registry.get_agent = MagicMock(return_value=gov_agent)

        claims = self.tax_service.calculate_liquidation_tax_claims(self.firm)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].creditor_id, "gov_real_id")
        self.assertEqual(claims[0].amount, 200.0) # 20% of 1000
        self.assertEqual(claims[0].tier, 3)
