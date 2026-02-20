import unittest
import logging
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.ai.api import Personality
from tests.utils.factories import create_household_config_dto
from simulation.models import Talent
from simulation.dtos.api import DecisionInputDTO
from modules.simulation.api import AgentCoreConfigDTO

class TestHouseholdIntegrationNew(unittest.TestCase):

    @unittest.skip('TODO: Fix integration test setup. BudgetEngine/ConsumptionEngine interaction results in empty orders.')
    def test_make_decision_integration(self):
        mock_decision_engine = MagicMock()
        mock_order = MagicMock()
        mock_order.side = 'BUY'
        mock_order.item_id = 'food'
        mock_order.quantity = 1.0
        mock_order.price_limit = 10.0
        mock_order.market_id = 'goods'
        mock_order.order_type = 'BUY'
        mock_order.price = 10.0
        mock_orders = [mock_order]
        mock_decision_engine.make_decisions.return_value = (mock_orders, ('TACTIC', 'AGGRESSIVE'))
        config = create_household_config_dto()
        core_config = AgentCoreConfigDTO(id=1, value_orientation='wealth_and_needs', initial_needs={'survival': 80.0}, name='Household_1', logger=logging.getLogger('test_household'), memory_interface=None)
        household = Household(core_config=core_config, engine=mock_decision_engine, talent=Talent(base_learning_rate=0.5, max_potential=1.0), goods_data=[{'id': 'food', 'initial_price': 10.0, 'utility_effects': {'survival': 10}}], personality=Personality.CONSERVATIVE, config_dto=config, initial_assets_record=1000.0)
        household._bio_state.needs = {'survival': 80.0}
        household.update_needs(100)
        self.assertIsNotNone(household.consumption_engine)
        self.assertIsNotNone(household.budget_engine)
        markets = {'goods': MagicMock()}
        market_data = {'housing_market': {'avg_rent_price': 50.0}, 'loan_market': {'interest_rate': 0.05}, 'goods_market': {'food_current_sell_price': 10.0}}
        current_time = 100
        mock_snapshot = MagicMock()
        mock_snapshot.labor.avg_wage = 10.0
        mock_snapshot.housing = MagicMock()
        mock_signal = MagicMock()
        mock_signal.best_ask = MagicMock()
        mock_signal.best_ask.amount = 10.0
        mock_snapshot.market_signals = {'food': mock_signal}
        input_dto = DecisionInputDTO(goods_data=[{'id': 'food', 'initial_price': 10.0, 'utility_effects': {'survival': 10}}, {'id': 'basic_food', 'initial_price': 10.0, 'utility_effects': {'survival': 10}}], market_data=market_data, current_time=current_time, market_snapshot=mock_snapshot, government_policy=None, fiscal_context=None, macro_context=None, stress_scenario_config=None, housing_system=None, agent_registry={})
        refined_orders, tactic = household.make_decision(input_dto)
        self.assertEqual(len(refined_orders), 1)
        self.assertEqual(refined_orders[0].item_id, 'food')
if __name__ == '__main__':
    unittest.main()