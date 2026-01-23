import pytest
from unittest.mock import MagicMock
from simulation.components.agent_lifecycle import AgentLifecycleComponent
from simulation.systems.api import LifecycleContext


@pytest.fixture
def lifecycle_component():
    owner = MagicMock()
    config = MagicMock()
    return AgentLifecycleComponent(owner, config)


def test_run_tick_execution_order(lifecycle_component):
    # Setup
    household = lifecycle_component.owner
    household.is_employed = True
    # Components on household
    household.labor_manager = MagicMock()
    household.economy_manager = MagicMock()
    household.psychology = MagicMock()

    context: LifecycleContext = {"household": household, "market_data": {}, "time": 1}

    # Execute
    lifecycle_component.run_tick(context)

    # Verify execution
    household.labor_manager.work.assert_called_with(8.0)
    household.economy_manager.pay_taxes.assert_called_once()
    household.psychology.update_needs.assert_called_with(1, {})


def test_run_tick_unemployed(lifecycle_component):
    household = lifecycle_component.owner
    household.is_employed = False
    household.labor_manager = MagicMock()
    household.economy_manager = MagicMock()
    household.psychology = MagicMock()

    context: LifecycleContext = {"household": household, "market_data": {}, "time": 1}

    lifecycle_component.run_tick(context)

    # Work hours should be 0.0
    household.labor_manager.work.assert_called_with(0.0)
