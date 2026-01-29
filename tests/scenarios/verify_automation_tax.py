import unittest
from unittest.mock import Mock, MagicMock
from simulation.decisions.firm.operations_manager import OperationsManager
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.models import Order

class TestAutomationTax(unittest.TestCase):
    def test_automation_tax_applied(self):
        # Setup DTOs
        config = MagicMock(spec=FirmConfigDTO)
        config.automation_cost_per_pct = 1000.0
        config.firm_safety_margin = 2000.0
        config.automation_tax_rate = 0.05
        # Add defaults for other calls in OperationsManager
        config.overstock_threshold = 1.2
        config.understock_threshold = 0.8
        config.production_adjustment_factor = 0.1
        config.firm_min_production_target = 10.0
        config.firm_max_production_target = 1000.0

        firm = MagicMock(spec=FirmStateDTO)
        firm.id = 1
        firm.automation_level = 0.5
        firm.assets = 10000.0
        firm.input_inventory = {}
        firm.inventory = {}
        firm.specialization = "food"
        firm.production_target = 100.0
        firm.revenue_this_turn = 5000.0 # needed for R&D logic if called, but agg=0.0

        context = MagicMock(spec=DecisionContext)
        context.config = config
        context.state = firm
        context.current_time = 100
        context.goods_data = [] # For goods_map
        context.market_data = {}

        guidance = {"target_automation": 0.6}
        aggressiveness = 1.0

        manager = OperationsManager()

        # Invoke via formulate_plan
        plan = manager.formulate_plan(context, capital_aggressiveness=aggressiveness, rd_aggressiveness=0.0, guidance=guidance)

        orders = plan.orders
        # Check for PAY_TAX order
        tax_orders = [o for o in orders if o.order_type == "PAY_TAX"]

        # Expected spend
        # Investable = 10000 - 2000 = 8000.
        # Cost = 1000 * (0.6 - 0.5)*100 = 1000 * 10 = 10000.
        # Budget = 8000 * (1.0 * 0.5) = 4000.
        # Actual = min(10000, 4000) = 4000.
        # Tax = 4000 * 0.05 = 200.

        self.assertEqual(len(tax_orders), 1)
        self.assertEqual(tax_orders[0].quantity, 200.0)
        self.assertEqual(tax_orders[0].item_id, "automation_tax")

if __name__ == '__main__':
    unittest.main()
