import pytest
from unittest.mock import Mock, MagicMock
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.core_agents import Household

@pytest.fixture
def mock_config():
    config = Mock()
    config.IMITATION_MUTATION_RATE = 0.1
    config.IMITATION_MUTATION_MAGNITUDE = 0.05
    config.TOP_PERFORMING_PERCENTILE = 0.1
    config.UNDER_PERFORMING_PERCENTILE = 0.5
    config.MITOSIS_Q_TABLE_MUTATION_RATE = None
    return config

@pytest.fixture
def mock_agents():
    agents = []
    for i in range(10):
        agent = Mock(spec=Household)
        agent.id = i
        agent._assets = float(i * 100) # 0, 100, ..., 900
        # Fix asset access for sorting (AITrainingManager might access .assets property)
        agent.assets = agent._assets

        # Mock Decision Engine and AI Engine
        agent.decision_engine = Mock()
        agent.decision_engine.ai_engine = Mock()

        # Mock Q-Table Managers
        agent.decision_engine.ai_engine.q_table_manager_strategy = Mock()
        agent.decision_engine.ai_engine.q_table_manager_strategy.q_table = {
            "state1": {"action1": 1.0}
        }

        agent.decision_engine.ai_engine.q_table_manager_tactic = Mock()
        agent.decision_engine.ai_engine.q_table_manager_tactic.q_table = {
            "stateA": {"actionA": 0.5}
        }

        # Delete V2 attributes to avoid iterating Mocks
        del agent.decision_engine.ai_engine.q_consumption
        del agent.decision_engine.ai_engine.q_work
        del agent.decision_engine.ai_engine.q_investment

        agents.append(agent)
    return agents

def test_get_top_performing_agents(mock_agents, mock_config):
    manager = AITrainingManager(mock_agents, mock_config)
    top_agents = manager._get_top_performing_agents(percentile=0.2)

    # Top 20% of 10 agents = 2 agents
    assert len(top_agents) == 2
    # Should be agent 9 (900) and agent 8 (800)
    assert top_agents[0].id == 9
    assert top_agents[1].id == 8

def test_get_under_performing_agents(mock_agents, mock_config):
    manager = AITrainingManager(mock_agents, mock_config)
    under_agents = manager._get_under_performing_agents(percentile=0.3)

    # Bottom 30% of 10 agents = 3 agents
    assert len(under_agents) == 3
    # Should be agent 0 (0), agent 1 (100), agent 2 (200) - sorted ascending
    assert under_agents[0].id == 0
    assert under_agents[1].id == 1
    assert under_agents[2].id == 2

def test_clone_and_mutate_q_table(mock_agents, mock_config):
    manager = AITrainingManager(mock_agents, mock_config)
    source = mock_agents[9] # Rich
    target = mock_agents[0] # Poor

    # Set distinct values for source
    source.decision_engine.ai_engine.q_table_manager_strategy.q_table = {
        "s1": {"a1": 10.0}
    }
    source.decision_engine.ai_engine.q_table_manager_tactic.q_table = {
        "t1": {"ta1": 5.0}
    }

    manager._clone_and_mutate_q_table(source, target)

    # Verify Strategy Table Cloned
    target_strategy_table = target.decision_engine.ai_engine.q_table_manager_strategy.q_table
    assert "s1" in target_strategy_table
    # Value should be close to 10.0 but potentially mutated
    assert 9.9 <= target_strategy_table["s1"]["a1"] <= 10.1

    # Verify Tactic Table Cloned
    target_tactic_table = target.decision_engine.ai_engine.q_table_manager_tactic.q_table
    assert "t1" in target_tactic_table
    # Value should be close to 5.0 but potentially mutated
    assert 4.9 <= target_tactic_table["t1"]["ta1"] <= 5.1

def test_clone_from_fittest_agent(mock_agents, mock_config):
    manager = AITrainingManager(mock_agents, mock_config)
    target = mock_agents[0]

    # Agent 9 is fittest (900 assets)
    fittest = mock_agents[9]
    fittest.decision_engine.ai_engine.q_table_manager_strategy.q_table = {"fit": {"win": 100.0}}

    manager.clone_from_fittest_agent(target)

    target_table = target.decision_engine.ai_engine.q_table_manager_strategy.q_table
    assert "fit" in target_table
    assert 99.0 <= target_table["fit"]["win"] <= 101.0

def test_run_imitation_learning_cycle(mock_agents, mock_config):
    manager = AITrainingManager(mock_agents, mock_config)

    # Mock _clone_and_mutate_q_table to verify calls
    manager._clone_and_mutate_q_table = Mock()

    manager.run_imitation_learning_cycle(current_tick=1000)

    # Should identify top and bottom agents and call clone
    # Top 10% (1 agent), Bottom 50% (5 agents)
    # Should call clone 5 times
    assert manager._clone_and_mutate_q_table.call_count == 5
