import pytest
from unittest.mock import Mock, ANY, patch
from modules.government.politics_system import PoliticsSystem
from modules.common.config.api import IConfigManager, GovernmentConfigDTO
from simulation.ai.enums import PoliticalParty
from simulation.dtos.api import SimulationState
from modules.government.political.api import VoteRecordDTO, IVoter

def test_process_tick_election_trigger():
    # Arrange
    mock_config_manager = Mock(spec=IConfigManager)

    # Setup Config
    initial_gov_config = GovernmentConfigDTO(
        income_tax_rate=0.1, corporate_tax_rate=0.2, sales_tax_rate=0.05,
        inheritance_tax_rate=0.0, wealth_tax_threshold=50000.0,
        annual_wealth_tax_rate=0.02, tax_brackets=[], gov_action_interval=30,
        rd_subsidy_rate=0.2, infrastructure_investment_cost=5000.0,
        infrastructure_tfp_boost=0.05, unemployment_benefit_ratio=0.0,
        stimulus_trigger_gdp_drop=-0.05, deficit_spending_enabled=True,
        deficit_spending_limit_ratio=0.30, emergency_budget_multiplier_cap=2.0,
        normal_budget_multiplier_cap=1.0, fiscal_sensitivity_alpha=0.5,
        potential_gdp_window=50, tax_rate_min=0.05, tax_rate_max=0.50,
        tax_rate_base=0.10, budget_allocation_min=0.1, budget_allocation_max=1.0,
        debt_ceiling_ratio=2.0, fiscal_stance_expansion_threshold=0.025,
        fiscal_stance_contraction_threshold=-0.025, fiscal_model="MIXED",
        public_edu_budget_ratio=0.20, government_policy_mode="AI_ADAPTIVE",
        target_inflation_rate=0.02, target_unemployment_rate=0.04,
        rl_learning_rate=0.1, rl_discount_factor=0.95, automation_tax_rate=0.05,
        policy_actuator_step_sizes=(0.01, 0.0025, 0.1), policy_actuator_bounds={}
    )
    mock_config_manager.get_config.return_value = initial_gov_config

    politics = PoliticsSystem(mock_config_manager)
    politics.election_cycle = 100

    # Mock State
    state = Mock(spec=SimulationState)
    state.time = 100 # Election time
    state.tracker = Mock()
    state.tracker.get_latest_indicators.return_value = {}
    state.market_data = {}

    # Mock Government
    gov = Mock()
    gov.ruling_party = PoliticalParty.BLUE
    gov.income_tax_rate = 0.1
    gov.corporate_tax_rate = 0.2
    state.primary_government = gov
    state.central_bank = Mock() # Required for make_policy_decision

    # Mock Households
    # 2 Households, both vote Disapprove (0.0) to trigger regime change
    # Must specify spec=IVoter for isinstance check
    h1 = Mock(spec=IVoter)
    h1.cast_vote.return_value = VoteRecordDTO(agent_id=1, tick=100, approval_value=0.0, primary_grievance="NONE", political_weight=1.0)

    h2 = Mock(spec=IVoter)
    h2.cast_vote.return_value = VoteRecordDTO(agent_id=2, tick=100, approval_value=0.0, primary_grievance="NONE", political_weight=1.0)

    state.households = [h1, h2]
    state.firms = [] # Ensure firms list exists for lobbying scan

    # Act
    politics.process_tick(state)

    # Assert
    # 1. Election happened, Red Won (because BLUE incumbent lost approval < 0.5)
    assert gov.ruling_party == PoliticalParty.RED

    # 2. Policy Mandate Applied (Red = High Tax)
    # Check if config updated
    mock_config_manager.update_config.assert_called_once()
    args, _ = mock_config_manager.update_config.call_args
    assert args[0] == "government"
    new_config = args[1]
    assert new_config.income_tax_rate == 0.25 # Red Platform

    # 3. Government state updated
    assert gov.income_tax_rate == 0.25

    # 4. make_policy_decision called
    gov.make_policy_decision.assert_called_once()

def test_process_tick_no_election():
    # Arrange
    mock_config_manager = Mock(spec=IConfigManager)
    politics = PoliticsSystem(mock_config_manager)
    politics.election_cycle = 100

    state = Mock(spec=SimulationState)
    state.time = 50 # No election
    state.tracker = Mock()
    state.tracker.get_latest_indicators.return_value = {}
    state.market_data = {}

    state.primary_government = Mock()
    state.households = []
    state.firms = [] # Ensure firms list exists
    state.central_bank = Mock() # Required for make_policy_decision

    # Act
    politics.process_tick(state)

    # Assert
    # No config update
    mock_config_manager.update_config.assert_not_called()

    # But make_policy_decision called
    state.primary_government.make_policy_decision.assert_called_once()
