import unittest
from unittest.mock import Mock, MagicMock
from simulation.decisions.corporate_manager import CorporateManager
from simulation.firms import Firm

class TestCompetitiveBidding(unittest.TestCase):
    def setUp(self):
        self.config = Mock()
        self.config.LABOR_MARKET_MIN_WAGE = 10.0
        self.config.GOODS = {}
        self.manager = CorporateManager(self.config)

    def _create_mock_firm(self, assets=10000.0, employees_count=5):
        firm = Mock(spec=Firm)
        firm.id = 1
        firm.assets = assets
        firm.employees = [Mock(id=i) for i in range(employees_count)]
        firm.employee_wages = {e.id: 10.0 for e in firm.employees}
        firm.production_target = 10.0
        firm.decision_engine = Mock()
        # Mock LoanMarket/Bank/Debt
        firm.decision_engine.loan_market = Mock()
        firm.decision_engine.loan_market.bank = Mock()
        firm.decision_engine.loan_market.bank.get_debt_summary.return_value = {'total_principal': 0.0}
        return firm

    def test_wage_increase_on_vacancy_solvent(self):
        """
        Scenario: Firm is solvent (Assets > Liabilities * 1.5) and has vacancies.
        Expectation: Wage increases (max 5%).
        """
        firm = self._create_mock_firm(assets=10000.0, employees_count=5)
        # Wage bill ~ 50. Liability = 0 (so uses WageBill * 10 = 500). Solvency = 10000/500 = 20 > 1.5.

        needed_labor = 10 # 5 vacancies
        current_offer = 20.0

        # Expected increase: 5 vacancies -> 5%
        expected_increase = 0.05
        expected_wage = 20.0 * (1.0 + expected_increase) # 21.0

        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertAlmostEqual(new_wage, expected_wage)

    def test_wage_increase_small_vacancy(self):
        """
        Scenario: 1 Vacancy.
        Expectation: 1% increase.
        """
        firm = self._create_mock_firm(assets=10000.0, employees_count=9)
        needed_labor = 10 # 1 vacancy
        current_offer = 20.0

        expected_wage = 20.0 * 1.01 # 20.2
        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertAlmostEqual(new_wage, expected_wage)

    def test_no_increase_when_insolvent_liability_based(self):
        """
        Scenario: Firm has high liabilities, causing Solvency < 1.5.
        Expectation: No wage increase despite vacancies.
        """
        firm = self._create_mock_firm(assets=1000.0, employees_count=5)
        # Set Debt to 800. Solvency = 1000 / 800 = 1.25 < 1.5
        firm.decision_engine.loan_market.bank.get_debt_summary.return_value = {'total_principal': 800.0}

        needed_labor = 10
        current_offer = 20.0

        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertEqual(new_wage, current_offer)

    def test_no_increase_when_insolvent_wage_bill_based(self):
        """
        Scenario: No debt, but assets are low relative to wage bill proxy.
        Solvency = Assets / (WageBill * 10).
        """
        firm = self._create_mock_firm(assets=600.0, employees_count=5)
        # WageBill = 5 * 10 = 50. Proxy = 500.
        # Solvency = 600 / 500 = 1.2 < 1.5.

        needed_labor = 10
        current_offer = 20.0

        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertEqual(new_wage, current_offer)

    def test_no_increase_no_vacancies(self):
        """
        Scenario: No vacancies.
        Expectation: No increase.
        """
        firm = self._create_mock_firm(assets=10000.0, employees_count=10)
        needed_labor = 10
        current_offer = 20.0

        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertEqual(new_wage, current_offer)

    def test_asset_ceiling_constraint(self):
        """
        Scenario: Proposed wage exceeds Assets / (Employees + 1).
        Expectation: Wage is capped.
        """
        # Assets = 100. Employees = 4. Ceiling = 100 / 5 = 20.
        firm = self._create_mock_firm(assets=100.0, employees_count=4)
        needed_labor = 6

        # Current offer is high (e.g., 25.0)
        current_offer = 25.0

        # Logic would try to increase it further or keep it.
        # But ceiling is 20.0.

        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertEqual(new_wage, 20.0)

    def test_min_wage_floor(self):
        """
        Scenario: Current offer is below min wage.
        Expectation: Bumped to min wage.
        """
        firm = self._create_mock_firm(assets=10000.0)
        needed_labor = 5
        current_offer = 5.0 # Below min wage 10.0

        new_wage = self.manager._adjust_wage_for_vacancies(firm, needed_labor, current_offer)

        self.assertEqual(new_wage, 10.0)

if __name__ == '__main__':
    unittest.main()
