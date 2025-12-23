import pytest
from unittest.mock import Mock, patch
import random

from simulation.ai.ai_training_manager import AITrainingManager
from simulation.core_agents import Household


@pytest.fixture
def mock_config():
    config = Mock()
    config.IMITATION_LEARNING_INTERVAL = 100
    config.IMITATION_MUTATION_RATE = 0.1
    config.IMITATION_MUTATION_MAGNITUDE = 0.05
    return config


@pytest.fixture
def mock_households():
    households = []
    for i in range(10):
        hh = Mock(spec=Household)
        hh.id = i
        hh.assets = i * 100.0
        decision_engine = Mock()
        decision_engine.ai_engine.q_table_manager_strategy.q_table = {
            "state": {"action": float(i)}
        }
        hh.decision_engine = decision_engine
        households.append(hh)
    return households


@pytest.fixture
def training_manager(mock_households, mock_config):
    return AITrainingManager(agents=mock_households, config_module=mock_config)


class TestAITrainingManager:
    def test_get_top_performing_agents(self, training_manager, mock_households):
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
            mock_choice.assert_called_once()
            # 9 agents should be cloned to (10 total agents - 1 top performer)
            assert mock_clone.call_count == 9
