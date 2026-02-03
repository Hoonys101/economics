import pytest
from unittest.mock import MagicMock, patch, mock_open
import statistics
import os

from modules.analysis.bubble_observatory import BubbleObservatory
from modules.market.housing_planner_api import HousingBubbleMetricsDTO

class TestBubbleObservatory:

    @pytest.fixture
    def simulation(self):
        sim = MagicMock()
        # Mock config_module attribute access
        sim.config_module.TICKS_PER_YEAR = 100
        sim.world_state = MagicMock()
        sim.world_state.time = 10
        sim.world_state.real_estate_units = []
        sim.world_state.calculate_total_money.return_value = 1000.0
        sim.world_state.transactions = []
        sim.agents = {}
        return sim

    def test_pir_calculation_normal(self, simulation):
        """
        Verify PIR calculation under normal conditions.
        Avg Price = 200,000
        Avg Income = 10,000
        PIR = 20.0
        """
        # Setup Prices
        unit1 = MagicMock()
        unit1.estimated_value = 200000
        simulation.world_state.real_estate_units = [unit1]

        # Setup Agents with Income
        agent1 = MagicMock()
        agent1.current_wage = 100 # Annual = 100 * 100 = 10000
        simulation.agents = {1: agent1}

        observatory = BubbleObservatory(simulation)

        # Patch open to prevent file writing
        with patch("builtins.open", mock_open()) as mock_file:
            metrics = observatory.collect_metrics()

        assert metrics["house_price_index"] == 200000
        # Avg Annual Income = 10000
        # PIR = 200000 / 10000 = 20.0
        assert metrics["pir"] == 20.0

    def test_pir_calculation_zero_income(self, simulation):
        """
        Verify PIR calculation when average income is zero.
        Should return 0.0 and not raise ZeroDivisionError.
        """
        # Setup Prices
        unit1 = MagicMock()
        unit1.estimated_value = 200000
        simulation.world_state.real_estate_units = [unit1]

        # Setup Agents with Zero Income
        agent1 = MagicMock()
        agent1.current_wage = 0
        simulation.agents = {1: agent1}

        observatory = BubbleObservatory(simulation)

        with patch("builtins.open", mock_open()):
            metrics = observatory.collect_metrics()

        assert metrics["pir"] == 0.0

    def test_pir_alarm(self, simulation):
        """
        Verify that a WARNING is logged if PIR > 20.0.
        """
        # Setup Prices (High)
        unit1 = MagicMock()
        unit1.estimated_value = 300000
        simulation.world_state.real_estate_units = [unit1]

        # Setup Agents (Low Income)
        agent1 = MagicMock()
        agent1.current_wage = 100 # Annual = 10000
        simulation.agents = {1: agent1}
        # PIR = 300000 / 10000 = 30.0 > 20.0

        observatory = BubbleObservatory(simulation)

        with patch("modules.analysis.bubble_observatory.logger") as mock_logger:
            with patch("builtins.open", mock_open()):
                metrics = observatory.collect_metrics()

            assert metrics["pir"] == 30.0
            mock_logger.warning.assert_called_once()
            args, _ = mock_logger.warning.call_args
            assert "High PIR detected: 30.00" in args[0]

    def test_csv_logging_structure(self, simulation):
        """
        Verify that the CSV log includes the PIR column.
        """
        # Setup dummy data
        simulation.world_state.real_estate_units = []
        simulation.agents = {}

        observatory = BubbleObservatory(simulation)

        # Mock file operations
        m_open = mock_open()
        with patch("builtins.open", m_open), patch("os.path.isfile", return_value=False):
            observatory.collect_metrics()

        # Check file writes
        handle = m_open()

        # Expect two calls to write: Header and Data
        # Header should include 'pir'
        # Data should include pir value

        # Join all write calls
        written_content = "".join([call.args[0] for call in handle.write.call_args_list])

        assert "tick,house_price_index,m2_growth_rate,new_mortgage_volume,average_ltv,average_dti,pir\n" in written_content
        # tick=10, others 0
        assert "10,0.00,0.000000,0.00,0.0000,0.0000,0.00\n" in written_content
