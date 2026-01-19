
import pytest
from unittest.mock import MagicMock, patch
from simulation.systems.event_system import EventSystem
from simulation.systems.commerce_system import CommerceSystem
from simulation.dtos.scenario import StressScenarioConfig
from simulation.core_agents import Household, Personality
from simulation.systems.api import EventContext, CommerceContext

class TestPhase28StressScenarios:

    @pytest.fixture
    def mock_households(self):
        h1 = MagicMock(spec=Household)
        h1.id = 1
        h1.assets = 1000.0
        h1.inventory = {}
        h1.is_active = True
        h1.is_employed = False
        # Personality.NORMAL is invalid, use CONSERVATIVE or another valid member
        h1.personality = Personality.CONSERVATIVE
        h1.adaptation_rate = 0.1
        h1.price_history = {"item1": []}
        h1.expected_inflation = {"item1": 0.0}

        h2 = MagicMock(spec=Household)
        h2.id = 2
        h2.assets = 5000.0 # Wealthy
        h2.is_active = True

        return [h1, h2]

    @pytest.fixture
    def mock_firms(self):
        f1 = MagicMock()
        f1.id = 101
        f1.type = "Farm"
        f1.productivity_factor = 1.0
        f1.assets = 10000.0
        return [f1]

    @pytest.fixture
    def event_system(self):
        config = MagicMock()
        return EventSystem(config)

    @pytest.fixture
    def commerce_system(self):
        config = MagicMock()
        reflux = MagicMock()
        return CommerceSystem(config, reflux)

    # --- Scenario 1: Hyperinflation ---

    def test_hyperinflation_trigger(self, event_system, mock_households, mock_firms):
        """Verify Cash Injection Trigger"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='hyperinflation',
            start_tick=10,
            demand_shock_cash_injection=0.5
        )

        context: EventContext = {
            "households": mock_households,
            "firms": mock_firms,
            "markets": {}
        }

        # Trigger event
        event_system.execute_scheduled_events(10, context, config)

        # Check household assets increased by 50%
        # mock_households[0].assets is a property on a mock, so we check if it was set
        # Since we mocked the object but not the attribute access completely for calc:
        # If we use MagicMock, operations like *= are recorded but values might not update if not real objects.
        # But here we used MagicMock which returns new MagicMocks on operations.
        # We need real objects or better mocks for calculation verification.
        # Let's verify the attribute set call.

        # Actually, for math operations on Mocks to work effectively for assertion,
        # we often need side_effect or specific setup.
        # Let's check if __imul__ was called with 1.5
        # Or simpler: configure the mock to behave like a float? No.

        # Let's inspect the code: `h.assets *= (1 + ...)`
        # This calls `h.assets.__imul__(1.5)`.
        # However, `h.assets` is likely a primitive in the real code, but here it's a Mock or float.
        # If I set h1.assets = 1000.0 (float), then `h1.assets *= 1.5` updates the attribute on the mock object instance.

        assert mock_households[0].assets == 1500.0
        assert mock_households[1].assets == 7500.0

    # --- Scenario 2: Deflation ---

    def test_deflation_asset_shock(self, event_system, mock_households, mock_firms):
        """Verify Asset Reduction Trigger"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            start_tick=20,
            asset_shock_reduction=0.2
        )

        context: EventContext = {
            "households": mock_households,
            "firms": mock_firms,
            "markets": {}
        }

        event_system.execute_scheduled_events(20, context, config)

        # 1000 * 0.8 = 800
        assert mock_households[0].assets == 800.0
        # Firm: 10000 * 0.8 = 8000
        assert mock_firms[0].assets == 8000.0

    def test_consumption_pessimism(self, commerce_system, mock_households):
        """Verify Consumption Collapse for Unemployed"""
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='deflation',
            consumption_pessimism_factor=0.3 # 30% reduction
        )

        # Setup Breeding Planner Mock to return consumption decisions
        planner = MagicMock()
        # Returns dict with lists matching household indices
        planner.decide_consumption_batch.return_value = {
            'consume': [10.0, 10.0],
            'buy': [0.0, 0.0],
            'price': 1.0
        }

        # Household 1: Unemployed -> Should be reduced
        mock_households[0].is_employed = False
        # Household 2: Employed -> Should NOT be reduced (mock doesn't have employed set, default False?)
        mock_households[1].is_employed = True

        context: CommerceContext = {
            "households": mock_households,
            "agents": {},
            "breeding_planner": planner,
            "household_time_allocation": {},
            "reflux_system": MagicMock(),
            "market_data": {},
            "config": MagicMock(),
            "time": 100
        }

        commerce_system.execute_consumption_and_leisure(context, config)

        # Verify consume calls
        # Household 1: 10.0 * 0.7 = 7.0
        mock_households[0].consume.assert_called_with("basic_food", 7.0, 100)
        # Household 2: 10.0 (No reduction)
        mock_households[1].consume.assert_called_with("basic_food", 10.0, 100)

    # --- Scenario 3: Supply Shock ---

    def test_supply_shock(self, event_system, mock_firms):
        config = StressScenarioConfig(
            is_active=True,
            scenario_name='supply_shock',
            start_tick=30,
            exogenous_productivity_shock={"Farm": 0.5}
        )

        context: EventContext = {
            "households": [],
            "firms": mock_firms,
            "markets": {}
        }

        event_system.execute_scheduled_events(30, context, config)

        # Firm 1 is Farm, Prod 1.0 -> 0.5
        assert mock_firms[0].productivity_factor == 0.5
