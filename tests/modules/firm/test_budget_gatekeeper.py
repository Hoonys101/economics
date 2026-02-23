import unittest
from typing import List, Dict
from modules.firm.components.budget_gatekeeper import BudgetGatekeeper
from modules.firm.api import ObligationDTO, PaymentPriority
from modules.system.api import DEFAULT_CURRENCY

class TestBudgetGatekeeper(unittest.TestCase):
    def setUp(self):
        self.gatekeeper = BudgetGatekeeper()

    def test_allocate_budget_sufficient_funds(self):
        liquid_assets = {DEFAULT_CURRENCY: 1000}
        obligations = [
            ObligationDTO(100, DEFAULT_CURRENCY, PaymentPriority.TAX, "gov", "Tax"),
            ObligationDTO(200, DEFAULT_CURRENCY, PaymentPriority.WAGE, "emp1", "Wage"),
        ]

        allocation = self.gatekeeper.allocate_budget(liquid_assets, obligations)

        self.assertEqual(len(allocation.approved_obligations), 2)
        self.assertEqual(len(allocation.rejected_obligations), 0)
        self.assertEqual(allocation.total_approved_amount_pennies, 300)
        self.assertEqual(allocation.remaining_liquidity_pennies, 700)
        self.assertFalse(allocation.is_insolvent)

    def test_allocate_budget_insufficient_funds_priority(self):
        liquid_assets = {DEFAULT_CURRENCY: 100}
        # Tax (50) + Wage (60) = 110 > 100
        # Should approve Tax (Priority 1) and Reject Wage (Priority 2)

        obligations = [
            ObligationDTO(60, DEFAULT_CURRENCY, PaymentPriority.WAGE, "emp1", "Wage"),
            ObligationDTO(50, DEFAULT_CURRENCY, PaymentPriority.TAX, "gov", "Tax"),
        ]

        allocation = self.gatekeeper.allocate_budget(liquid_assets, obligations)

        self.assertEqual(len(allocation.approved_obligations), 1)
        self.assertEqual(allocation.approved_obligations[0].priority, PaymentPriority.TAX)

        self.assertEqual(len(allocation.rejected_obligations), 1)
        self.assertEqual(allocation.rejected_obligations[0].priority, PaymentPriority.WAGE)

        self.assertEqual(allocation.remaining_liquidity_pennies, 50)
        self.assertTrue(allocation.is_insolvent) # Wage rejected

    def test_insolvency_check_optional_obligations(self):
        liquid_assets = {DEFAULT_CURRENCY: 100}
        # Tax (50) + Marketing (60) = 110 > 100
        # Approve Tax, Reject Marketing.
        # Should NOT be insolvent because Marketing is not mandatory.

        obligations = [
            ObligationDTO(60, DEFAULT_CURRENCY, PaymentPriority.MARKETING, "gov", "Marketing"),
            ObligationDTO(50, DEFAULT_CURRENCY, PaymentPriority.TAX, "gov", "Tax"),
        ]

        allocation = self.gatekeeper.allocate_budget(liquid_assets, obligations)

        self.assertEqual(len(allocation.approved_obligations), 1)
        self.assertEqual(allocation.approved_obligations[0].priority, PaymentPriority.TAX)

        self.assertEqual(len(allocation.rejected_obligations), 1)
        self.assertEqual(allocation.rejected_obligations[0].priority, PaymentPriority.MARKETING)

        self.assertFalse(allocation.is_insolvent)

if __name__ == '__main__':
    unittest.main()
