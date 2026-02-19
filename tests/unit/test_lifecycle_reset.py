import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.dtos.api import SimulationState

class TestLifecycleReset:
    def test_reset_tick_state(self):
        manager = AgentLifecycleManager(
            config_module=MagicMock(),
            demographic_manager=MagicMock(),
            inheritance_manager=MagicMock(),
            firm_system=MagicMock(),
            settlement_system=MagicMock(),
            public_manager=MagicMock(),
            logger=MagicMock(),
            household_factory=MagicMock()
        )

        household = MagicMock()
        household.is_active = True

        firm = MagicMock()
        firm.is_active = True

        state = MagicMock(spec=SimulationState)
        state.households = [household]
        state.firms = [firm]

        manager.reset_agents_tick_state(state)

        household.reset_tick_state.assert_called_once()
        firm.reset.assert_called_once()

    def test_household_reset_logic(self):
        # We can mock Household state container
        agent = MagicMock()
        # Bind the real method to the mock
        agent.reset_tick_state = Household.reset_tick_state.__get__(agent, Household)
        agent.logger = MagicMock()

        # Mock state DTO
        agent._econ_state = MagicMock()
        agent._econ_state.labor_income_this_tick_pennies = 100
        agent._econ_state.capital_income_this_tick_pennies = 50
        agent._econ_state.current_consumption = 10.5
        agent._econ_state.current_food_consumption = 5.0

        agent.id = 1

        agent.reset_tick_state()

        assert agent._econ_state.labor_income_this_tick_pennies == 0
        assert agent._econ_state.capital_income_this_tick_pennies == 0
        assert agent._econ_state.current_consumption == 0.0
        assert agent._econ_state.current_food_consumption == 0.0
