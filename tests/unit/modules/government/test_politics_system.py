import pytest
from unittest.mock import Mock, ANY
from modules.government.politics_system import PoliticsSystem
from modules.common.config.api import IConfigManager, GovernmentConfigDTO
import dataclasses

def test_enact_new_tax_policy():
    # Arrange
    mock_config_manager = Mock(spec=IConfigManager)

    # Setup initial config
    initial_gov_config = GovernmentConfigDTO(
        income_tax_rate=0.1,
        corporate_tax_rate=0.2,
        sales_tax_rate=0.05,
        inheritance_tax_rate=0.0,
        wealth_tax_threshold=50000.0,
        annual_wealth_tax_rate=0.02,
        tax_brackets=[],
        gov_action_interval=30,
        rd_subsidy_rate=0.2,
        infrastructure_investment_cost=5000.0,
        infrastructure_tfp_boost=0.05,
        unemployment_benefit_ratio=0.0,
        stimulus_trigger_gdp_drop=-0.05,
        deficit_spending_enabled=True,
        deficit_spending_limit_ratio=0.30,
        emergency_budget_multiplier_cap=2.0,
        normal_budget_multiplier_cap=1.0,
        fiscal_sensitivity_alpha=0.5,
        potential_gdp_window=50,
        tax_rate_min=0.05,
        tax_rate_max=0.50,
        tax_rate_base=0.10,
        budget_allocation_min=0.1,
        budget_allocation_max=1.0,
        debt_ceiling_ratio=2.0,
        fiscal_stance_expansion_threshold=0.025,
        fiscal_stance_contraction_threshold=-0.025,
        fiscal_model="MIXED",
        public_edu_budget_ratio=0.20,
        government_policy_mode="AI_ADAPTIVE",
        target_inflation_rate=0.02,
        target_unemployment_rate=0.04,
        rl_learning_rate=0.1,
        rl_discount_factor=0.95,
        automation_tax_rate=0.05,
        policy_actuator_step_sizes=(0.01, 0.0025, 0.1),
        policy_actuator_bounds={}
    )

    mock_config_manager.get_config.return_value = initial_gov_config

    politics = PoliticsSystem(mock_config_manager)
    simulation_state = Mock()

    # Act
    politics.enact_new_tax_policy(simulation_state)

    # Assert
    # Verify get_config was called
    mock_config_manager.get_config.assert_called_with("government", GovernmentConfigDTO)

    # Verify update_config was called with a GovernmentConfigDTO
    # In our placeholder logic, the rate doesn't change, but it should still call update
    mock_config_manager.update_config.assert_called_once()
    args, _ = mock_config_manager.update_config.call_args
    domain_name, new_config = args
    assert domain_name == "government"
    assert isinstance(new_config, GovernmentConfigDTO)
    assert new_config.income_tax_rate == 0.1
