import pytest
from unittest.mock import Mock, MagicMock, patch
from simulation.orchestration.phases import Phase1_Decision
from simulation.dtos.api import SimulationState, DecisionInputDTO
from modules.system.api import (
    MarketSnapshotDTO, HousingMarketSnapshotDTO, LoanMarketSnapshotDTO,
    LaborMarketSnapshotDTO
)

def create_mock_snapshot(time=100):
    housing_snapshot = HousingMarketSnapshotDTO(for_sale_units=[], units_for_rent=[], avg_rent_price=100.0, avg_sale_price=24000.0)
    loan_snapshot = LoanMarketSnapshotDTO(interest_rate=0.05)
    labor_snapshot = LaborMarketSnapshotDTO(avg_wage=0.0)

    return MarketSnapshotDTO(
        tick=time,
        market_signals={},
        housing=housing_snapshot,
        loan=loan_snapshot,
        labor=labor_snapshot,
        market_data={}
    )

class TestPhase1DecisionRefactor:
    def test_execute_flow(self):
        # Mock Dependencies
        world_state = MagicMock()
        state = MagicMock(spec=SimulationState)
        state.time = 100
        state.tracker = MagicMock() # Mock tracker
        state.stock_market = MagicMock() # Mock stock_market
        state.stock_market.get_daily_avg_price.return_value = 10.0 # Return mock float
        state.goods_data = {} # Mock goods_data
        state.markets = {"market1": MagicMock()}
        state.real_estate_units = [] # Mock empty list
        state.firms = []
        state.households = []
        state.agents = {}
        state.government = MagicMock()
        state.bank = MagicMock()
        state.central_bank = MagicMock()
        state.config_module = MagicMock()
        state.config_module.MACRO_PORTFOLIO_ADJUSTMENT_ENABLED = False
        state.config_module.SALES_TAX_RATE = 0.05
        state.config_module.MAX_WORK_HOURS = 10.0
        state.config_module.HOURS_PER_TICK = 24.0
        state.config_module.SHOPPING_HOURS = 2.0

        world_state.commerce_system = MagicMock()
        world_state.commerce_system.plan_consumption_and_leisure.return_value = ({}, [])

        # Prepare mocking factories
        # Phase1_Decision instantiates factories in __init__
        # We need to mock them *after* instantiation or patch the classes

        with patch('simulation.orchestration.phases.decision.DecisionInputFactory') as MockInputFactory, \
             patch('simulation.orchestration.phases.decision.MarketSnapshotFactory') as MockSnapshotFactory, \
             patch('simulation.orchestration.phases.decision.prepare_market_data') as mock_prepare_data:

            mock_prepare_data.return_value = {}

            phase = Phase1_Decision(world_state)

            mock_snapshot_factory_instance = MockSnapshotFactory.return_value
            snapshot = create_mock_snapshot(state.time)
            mock_snapshot_factory_instance.create_snapshot.return_value = snapshot

            mock_input_factory_instance = MockInputFactory.return_value
            # dataclasses.replace requires a real dataclass instance
            mock_input_factory_instance.create_decision_input.return_value = DecisionInputDTO(
                market_snapshot=snapshot,
                goods_data={},
                market_data={},
                current_time=100
            )

            # Note: We mocked MarketSnapshotFactory class, and Phase1_Decision instantiates it in __init__.
            # So `phase.snapshot_factory` is the mock instance created during __init__.
            # `MockSnapshotFactory.return_value` gives us that instance.
            # We already set `mock_snapshot_factory_instance.create_snapshot.return_value = snapshot` above.

            # Execute
            phase.execute(state)

            # Verify Factory Calls
            # Use `phase.snapshot_factory` which is the actual mock instance used by the phase
            phase.snapshot_factory.create_snapshot.assert_called_once_with(state)
            mock_input_factory_instance.create_decision_input.assert_called_once()

            # Verify market data preparation
            mock_prepare_data.assert_called_once_with(state)

    def test_dispatch_logic(self):
        # Test that _dispatch_firm_decisions and _dispatch_household_decisions are called
        # (Implicitly tested via execute, but we can check if agents make decisions)

        world_state = MagicMock()
        world_state.commerce_system = MagicMock()
        world_state.commerce_system.plan_consumption_and_leisure.return_value = ({}, [])

        state = MagicMock(spec=SimulationState)
        state.time = 100
        state.tracker = MagicMock() # Mock tracker
        state.stock_market = MagicMock() # Mock stock_market
        state.stock_market.get_daily_avg_price.return_value = 10.0 # Return mock float
        state.bank = MagicMock() # Mock bank
        state.goods_data = {} # Mock goods_data
        state.markets = {}
        state.real_estate_units = [] # Mock empty list
        state.agents = {}
        state.government = MagicMock()
        state.central_bank = MagicMock()
        state.config_module = MagicMock()
        state.config_module.MAX_WORK_HOURS = 10.0
        state.config_module.HOURS_PER_TICK = 24.0
        state.config_module.SHOPPING_HOURS = 2.0

        firm = MagicMock()
        firm.is_active = True
        firm.make_decision.return_value = ([], None) # Legacy return
        firm.get_agent_data.return_value = {}

        household = MagicMock()
        household._bio_state.is_active = True
        household.make_decision.return_value = ([], None) # Legacy return
        household.get_agent_data.return_value = {}

        state.firms = [firm]
        state.households = [household]

        with patch('simulation.orchestration.phases.decision.DecisionInputFactory') as MockInputFactory, \
             patch('simulation.orchestration.phases.decision.MarketSnapshotFactory') as MockSnapshotFactory, \
             patch('simulation.orchestration.phases.decision.prepare_market_data', return_value={}):

            phase = Phase1_Decision(world_state)

            mock_snapshot_factory_instance = MockSnapshotFactory.return_value
            snapshot = create_mock_snapshot(state.time)
            mock_snapshot_factory_instance.create_snapshot.return_value = snapshot

            # Setup factory to return real DTO
            mock_input_factory_instance = MockInputFactory.return_value
            mock_input_factory_instance.create_decision_input.return_value = DecisionInputDTO(
                market_snapshot=snapshot,
                goods_data={},
                market_data={},
                current_time=100
            )

            phase.execute(state)

            firm.make_decision.assert_called_once()
            household.make_decision.assert_called_once()
