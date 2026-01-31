import unittest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.ai.api import Personality
from tests.utils.factories import create_household_config_dto
from simulation.models import Talent

class TestHouseholdIntegrationNew(unittest.TestCase):
    def test_make_decision_integration(self):
        # Create real household with mocked dependencies
        mock_decision_engine = MagicMock()
        mock_decision_engine.ai_engine = MagicMock()

        # Mock engine to return some orders
        mock_order = MagicMock()
        mock_order.side = "BUY"
        mock_order.item_id = "food"
        mock_order.quantity = 1.0
        mock_order.price_limit = 10.0
        mock_order.market_id = "goods"
        mock_order.order_type = "BUY" # Legacy compat if needed
        mock_order.price = 10.0 # Legacy compat if needed

        mock_orders = [mock_order]
        mock_decision_engine.make_decisions.return_value = (mock_orders, ("TACTIC", "AGGRESSIVE"))

        config = create_household_config_dto()

        household = Household(
            id=1,
            talent=Talent(base_learning_rate=0.5, max_potential=1.0),
            goods_data=[{"id": "food", "initial_price": 10.0}],
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=mock_decision_engine,
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            config_dto=config
        )

        # Verify components are initialized
        self.assertIsNotNone(household.consumption_manager)
        self.assertIsNotNone(household.decision_unit)

        # Call make_decision
        markets = {"goods": MagicMock()}
        market_data = {"housing_market": {"avg_rent_price": 50.0}, "loan_market": {"interest_rate": 0.05}}
        current_time = 100

        refined_orders, tactic = household.make_decision(
            markets=markets,
            goods_data=[],
            market_data=market_data,
            current_time=current_time
        )

        # Verify DecisionUnit was used (indirectly via result)
        # The orders should be passed through (or modified)
        self.assertEqual(len(refined_orders), 1)
        self.assertEqual(refined_orders[0].item_id, "food")

        # Verify state update (e.g. shadow wage logic in DecisionUnit)
        # Initial shadow wage is 0.0 (from init) or calculated.
        # Household init sets shadow_reservation_wage = 0.0?
        # Let's check init.
        # It sets shadow_reservation_wage = 0.0.
        # DecisionUnit logic: if 0, sets to expected_wage (10.0).
        # Then applies decay if unemployed.
        # So it should be > 0.0 after update.
        self.assertGreater(household._econ_state.shadow_reservation_wage, 0.0)

if __name__ == '__main__':
    unittest.main()
