import pytest
from unittest.mock import MagicMock, patch
from modules.household.factory import HouseholdFactory
from modules.household.api import HouseholdFactoryContext
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.simulation.api import AgentCoreConfigDTO
from simulation.core_agents import Household

class TestHouseholdFactory:

    @pytest.fixture
    def context(self):
        context = MagicMock(spec=HouseholdFactoryContext)
        context.household_config_dto = MagicMock(spec=HouseholdConfigDTO)
        context.core_config_module = MagicMock()
        # Set config attributes explicitly to avoid MagicMocks
        context.core_config_module.DEFAULT_VALUE_ORIENTATION = "Growth"
        context.core_config_module.INITIAL_NEEDS = {}
        context.core_config_module.NEWBORN_ENGINE_TYPE = "AIDriven"
        context.core_config_module.MITOSIS_MUTATION_PROBABILITY = 0.1
        context.core_config_module.initial_household_age_range = (20, 60)
        context.core_config_module.INITIAL_WAGE = 10.0
        context.core_config_module.initial_household_assets_mean = 1000

        context.goods_data = []
        context.settlement_system = MagicMock()
        context.markets = {}
        context.ai_training_manager = MagicMock()
        context.memory_system = None
        context.loan_market = MagicMock()
        return context

    def test_create_newborn_zero_sum(self, context):
        factory = HouseholdFactory(context)
        parent = MagicMock(spec=Household)
        parent.id = 1
        parent.generation = 1
        parent.talent = MagicMock()
        parent.personality = MagicMock()
        parent.value_orientation = "Growth"

        # Mocking parent.talent structure for copy
        parent.talent.base_learning_rate = 1.0

        gift_amount = 1000

        with patch('modules.household.factory.Household') as MockHousehold:
            child_instance = MagicMock()
            MockHousehold.return_value = child_instance
            child_instance.id = 2

            # Setup load_state to verify initial assets 0
            child_instance.load_state = MagicMock()

            child = factory.create_newborn(parent, new_id=2, initial_assets=gift_amount, current_tick=10)

            # Verify instantiation used 0 assets
            call_args = MockHousehold.call_args
            assert call_args is not None
            _, kwargs = call_args
            assert kwargs['initial_assets_record'] == 0

            # Verify settlement transfer called
            context.settlement_system.transfer.assert_called_once_with(
                sender=parent,
                receiver=child,
                amount=gift_amount,
                transaction_type="BIRTH_GIFT",
                tick=10
            )

    def test_create_immigrant(self, context):
        factory = HouseholdFactory(context)
        initial_assets = 5000

        with patch('modules.household.factory.Household') as MockHousehold:
            immigrant = factory.create_immigrant(new_id=3, current_tick=10, initial_assets=initial_assets)

            # Verify instantiated with assets (Magic Money)
            call_args = MockHousehold.call_args
            _, kwargs = call_args
            assert kwargs['initial_assets_record'] == initial_assets

            # Verify NO settlement transfer (magic money)
            context.settlement_system.transfer.assert_not_called()
