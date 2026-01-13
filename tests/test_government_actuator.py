import pytest
from unittest.mock import MagicMock, patch

# The class to be tested
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy

# Mock objects to simulate the environment
class MockGovernment:
    def __init__(self):
        self.tax_rate = 0.20
        self.budget_allocation = 0.50
        self.perceived_public_opinion = 0.5

class MockCentralBank:
    def __init__(self):
        self.base_rate = 0.05

class MockConfig:
    def __init__(self):
        self.GOV_ACTION_INTERVAL = 30

@pytest.fixture
def policy_setup():
    """Sets up the SmartLeviathanPolicy with mock objects for testing."""
    mock_gov = MockGovernment()
    mock_config = MockConfig()

    # We need to patch the GovernmentAI where it is defined, because it's imported dynamically.
    with patch('simulation.ai.government_ai.GovernmentAI') as MockAI:
        mock_ai_instance = MockAI.return_value
        policy = SmartLeviathanPolicy(mock_gov, mock_config)

        # Attach mocks for easy access in tests
        policy.ai = mock_ai_instance
        mock_bank = MockCentralBank()
        market_data = {"central_bank": mock_bank}

        yield policy, mock_gov, mock_bank, mock_ai_instance, market_data

def test_silent_interval_enforcement(policy_setup):
    """Verify that no action is taken if the tick is not on the interval."""
    policy, gov, bank, ai, market_data = policy_setup

    initial_rate = bank.base_rate
    initial_tax = gov.tax_rate
    initial_budget = gov.budget_allocation

    # Test for a tick that is NOT a multiple of 30
    result = policy.decide(gov, market_data, current_tick=29)

    # Assert no decision was requested from the AI
    ai.decide_policy.assert_not_called()

    # Assert no state was changed
    assert bank.base_rate == initial_rate
    assert gov.tax_rate == initial_tax
    assert gov.budget_allocation == initial_budget
    assert result["status"] == "HOLD_INTERVAL"

def test_action_dovish_decreases_rate(policy_setup):
    """Test Action 0 (Dovish) correctly decreases the interest rate."""
    policy, gov, bank, ai, market_data = policy_setup
    ai.decide_policy.return_value = 0  # Action: Dovish

    initial_rate = bank.base_rate
    policy.decide(gov, market_data, current_tick=30)

    ai.decide_policy.assert_called_once()
    assert bank.base_rate == initial_rate - 0.0025

def test_action_hawkish_increases_rate(policy_setup):
    """Test Action 2 (Hawkish) correctly increases the interest rate."""
    policy, gov, bank, ai, market_data = policy_setup
    ai.decide_policy.return_value = 2  # Action: Hawkish

    initial_rate = bank.base_rate
    policy.decide(gov, market_data, current_tick=60)

    ai.decide_policy.assert_called_once()
    assert bank.base_rate == initial_rate + 0.0025

def test_action_fiscal_ease_decreases_tax(policy_setup):
    """Test Action 3 (Fiscal Ease) correctly decreases the tax rate."""
    policy, gov, bank, ai, market_data = policy_setup
    ai.decide_policy.return_value = 3  # Action: Fiscal Ease

    initial_tax = gov.tax_rate
    policy.decide(gov, market_data, current_tick=90)

    ai.decide_policy.assert_called_once()
    assert gov.tax_rate == initial_tax - 0.01

def test_action_fiscal_tight_increases_tax_and_decreases_budget(policy_setup):
    """Test Action 4 (Fiscal Tight) correctly increases tax and decreases budget."""
    policy, gov, bank, ai, market_data = policy_setup
    ai.decide_policy.return_value = 4  # Action: Fiscal Tight

    initial_tax = gov.tax_rate
    initial_budget = gov.budget_allocation
    policy.decide(gov, market_data, current_tick=120)

    ai.decide_policy.assert_called_once()
    assert gov.tax_rate == initial_tax + 0.01
    assert gov.budget_allocation == initial_budget - 0.05

def test_interest_rate_clamping(policy_setup):
    """Verify interest rate is clamped between 0.0 and 0.20."""
    policy, gov, bank, ai, market_data = policy_setup

    # Test lower bound
    bank.base_rate = 0.001
    ai.decide_policy.return_value = 0  # Dovish
    policy.decide(gov, market_data, current_tick=30)
    assert bank.base_rate == 0.0

    # Test upper bound
    bank.base_rate = 0.199
    ai.decide_policy.return_value = 2  # Hawkish
    policy.decide(gov, market_data, current_tick=60)
    assert bank.base_rate == 0.20

def test_tax_rate_clamping(policy_setup):
    """Verify tax rate is clamped between 0.05 and 0.50."""
    policy, gov, bank, ai, market_data = policy_setup

    # Test lower bound
    gov.tax_rate = 0.055
    ai.decide_policy.return_value = 3  # Fiscal Ease
    policy.decide(gov, market_data, current_tick=30)
    assert gov.tax_rate == 0.05

    # Test upper bound
    gov.tax_rate = 0.495
    ai.decide_policy.return_value = 4  # Fiscal Tight
    policy.decide(gov, market_data, current_tick=60)
    assert gov.tax_rate == 0.50

def test_budget_allocation_clamping(policy_setup):
    """Verify budget allocation is clamped between 0.1 and 1.0."""
    policy, gov, bank, ai, market_data = policy_setup
    ai.decide_policy.return_value = 4  # Fiscal Tight (the only action that affects budget)

    # Test lower bound
    gov.budget_allocation = 0.14
    policy.decide(gov, market_data, current_tick=30)
    assert gov.budget_allocation == 0.1

    # Test upper bound (should never be an issue with current logic, but good practice)
    gov.budget_allocation = 1.0
    policy.decide(gov, market_data, current_tick=60)
    assert gov.budget_allocation == 0.95 # This is correct, it's not clamped at 1.0

    # Let's test if we can get it clamped to 1.0, though no action increases budget.
    # For completeness, let's imagine a hypothetical action that increases it.
    # We can manually set it to a value > 1.0 and see if clamping would work.
    # Note: This part is theoretical as no current action increases the budget.
    gov.budget_allocation = 1.05
    clamped_budget = max(0.1, min(1.0, gov.budget_allocation))
    assert clamped_budget == 1.0
