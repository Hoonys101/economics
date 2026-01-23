import pytest
from unittest.mock import Mock, patch
import random

from simulation.ai.ai_training_manager import AITrainingManager
from simulation.core_agents import Household


@pytest.fixture
def mock_config(golden_config):
    if golden_config:
        config = golden_config
    else:
        config = Mock()
    config.IMITATION_LEARNING_INTERVAL = 100
    config.IMITATION_MUTATION_RATE = 0.1
    config.IMITATION_MUTATION_MAGNITUDE = 0.05
    config.MITOSIS_Q_TABLE_MUTATION_RATE = None # Ensure explicit None
    config.TOP_PERFORMING_PERCENTILE = 0.1
    config.UNDER_PERFORMING_PERCENTILE = 0.5
    return config


@pytest.fixture
def mock_households(golden_households):
    # Use golden_households if available, but we need 10 of them with specific assets
    # and structure for the test logic.
    if not golden_households:
        pytest.skip("Golden households fixture is empty.")

    households = []
    base_agent = golden_households[0]

    for i in range(10):
        hh = Mock(spec=Household)
        hh.id = i
        hh._assets = float(i * 100.0)

        # Ensure deep structure exists
        decision_engine = Mock()
        # V1 legacy structure
        decision_engine.ai_engine.q_table_manager_strategy.q_table = {
            "state": {"action": float(i)}
        }

        # Make sure q_table_manager_tactic.q_table is also iterable because _clone_and_mutate_q_table accesses it
        decision_engine.ai_engine.q_table_manager_tactic.q_table = {}

        # Remove V2 attributes to prevent code entering V2 blocks which require complex setup
        # The code checks hasattr(source_ai, "q_consumption"). Mock has everything by default.
        if hasattr(decision_engine.ai_engine, "q_consumption"):
            del decision_engine.ai_engine.q_consumption
        if hasattr(decision_engine.ai_engine, "q_work"):
            del decision_engine.ai_engine.q_work
        if hasattr(decision_engine.ai_engine, "q_investment"):
            del decision_engine.ai_engine.q_investment

        hh.decision_engine = decision_engine

        households.append(hh)

    return households


@pytest.fixture
def training_manager(mock_households, mock_config):
    return AITrainingManager(agents=mock_households, config_module=mock_config)


class TestAITrainingManager:
    def test_get_top_performing_agents(self, training_manager, mock_households):
        # Percentile 0.2 means top 20%
        top_performers = training_manager._get_top_performing_agents(percentile=0.2)
        assert len(top_performers) == 2
        assert top_performers[0].assets == 900.0
        assert top_performers[1].assets == 800.0

    def test_clone_and_mutate_q_table(self, training_manager, mock_households):
        source_agent = mock_households[9]  # Richest agent
        target_agent = mock_households[0]  # Poorest agent

        original_q_value = (
            source_agent.decision_engine.ai_engine.q_table_manager_strategy.q_table[
                "state"
            ]["action"]
        )

        with (
            patch.object(random, "random", return_value=0.05),
            patch.object(random, "uniform", return_value=0.01),
        ):
            training_manager._clone_and_mutate_q_table(source_agent, target_agent)

        new_q_value = (
            target_agent.decision_engine.ai_engine.q_table_manager_strategy.q_table[
                "state"
            ]["action"]
        )

        assert new_q_value != original_q_value
        assert new_q_value == original_q_value + 0.01

    def test_run_imitation_learning_cycle(self, training_manager, mock_households):
        mock_role_model = mock_households[9]  # Richest agent
        with (
            patch.object(
                training_manager,
                "_get_top_performing_agents",
                return_value=[mock_role_model],
            ) as mock_get_top,
            patch.object(training_manager, "_clone_and_mutate_q_table") as mock_clone,
            patch.object(random, "choice", return_value=mock_role_model) as mock_choice,
        ):
            training_manager.run_imitation_learning_cycle(100)

            mock_get_top.assert_called_once()

            # With 10 households, top 0.1 (1 agent), bottom 0.5 (5 agents).
            # 5 learners will call choice and clone.
            assert mock_choice.call_count == 5
            assert mock_clone.call_count == 5
