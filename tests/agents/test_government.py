import pytest
from unittest.mock import MagicMock, Mock
from simulation.agents.government import Government


@pytest.fixture
def government_setup(mocker):
    # Mocking patches
    mock_tax_agency_cls = mocker.patch("simulation.agents.government.TaxAgency")
    mock_education_ministry_cls = mocker.patch(
        "simulation.agents.government.MinistryOfEducation"
    )

    mock_tax_agency_instance = mock_tax_agency_cls.return_value
    mock_education_ministry_instance = mock_education_ministry_cls.return_value

    mock_config = Mock()
    mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    mock_config.TICKS_PER_YEAR = 100
    mock_config.INCOME_TAX_RATE = 0.1  # This is the initial rate
    mock_config.CORPORATE_TAX_RATE = 0.2
    mock_config.TAX_MODE = "PROGRESSIVE"

    government = Government(id=1, initial_assets=100000, config_module=mock_config)
    # Manually set a different tax rate on the government instance to test that
    # the *current* rate is passed, not the initial config rate.
    government.income_tax_rate = 0.15
    government.corporate_tax_rate = 0.25

    return {
        "government": government,
        "mock_tax_agency": mock_tax_agency_instance,
        "mock_education_ministry": mock_education_ministry_instance,
        "mock_config": mock_config,
    }


def test_calculate_income_tax_delegation(government_setup):
    env = government_setup
    income = 50000
    survival_cost = 15000

    env["government"].calculate_income_tax(income, survival_cost)

    env["mock_tax_agency"].calculate_income_tax.assert_called_once_with(
        income,
        survival_cost,
        env["government"].income_tax_rate,  # Should pass the current rate (0.15)
        "PROGRESSIVE",
    )


def test_calculate_corporate_tax_delegation(government_setup):
    env = government_setup
    profit = 100000

    env["government"].calculate_corporate_tax(profit)

    env["mock_tax_agency"].calculate_corporate_tax.assert_called_once_with(
        profit,
        env["government"].corporate_tax_rate,  # Should pass the current rate (0.25)
    )


def test_collect_tax_delegation(government_setup):
    """Test if collect_tax delegates to TaxAgency."""
    env = government_setup
    amount = 1000
    tax_type = "income"
    source_id = 101
    current_tick = 50

    env["government"].collect_tax(amount, tax_type, source_id, current_tick)

    env["mock_tax_agency"].collect_tax.assert_called_once_with(
        env["government"], amount, tax_type, source_id, current_tick
    )


def test_run_public_education_delegation(government_setup):
    """Test if run_public_education delegates to MinistryOfEducation."""
    env = government_setup
    mock_agent1 = Mock()
    mock_agent1.education_level = 1
    agents = [mock_agent1]

    env["government"].run_public_education(agents, env["mock_config"], 100, None)

    env["mock_education_ministry"].run_public_education.assert_called_once()


@pytest.fixture
def deficit_government_setup():
    mock_config = Mock()
    mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    mock_config.TICKS_PER_YEAR = 100
    mock_config.DEFICIT_SPENDING_ENABLED = True
    mock_config.DEFICIT_SPENDING_LIMIT_RATIO = 0.30

    government = Government(id=1, initial_assets=1000, config_module=mock_config)

    # Mock sensory data for GDP
    mock_sensory_data = Mock()
    mock_sensory_data.current_gdp = 10000
    government.sensory_data = mock_sensory_data

    # Mock FinanceSystem
    mock_finance = Mock()
    mock_finance.issue_treasury_bonds.return_value = (
        True  # Simulate successful bond issuance
    )
    government.finance_system = mock_finance

    return government


def test_deficit_spending_allowed_within_limit(deficit_government_setup):
    """Test that the government can spend more than its assets, creating debt."""
    government = deficit_government_setup
    government._assets = 100
    target_agent = Mock()
    target_agent._assets = 0

    # Debt limit = 10000 * 0.30 = 3000
    # Spending 500 will result in assets of -400, which is within the limit
    amount_paid = government.provide_household_support(
        target_agent, 500, current_tick=1
    )

    assert amount_paid == 500
    assert government.assets == -400
    assert target_agent.assets == 500

    # Finalize tick to update debt
    government.finalize_tick(1)
    assert government.total_debt == 400


def test_deficit_spending_blocked_beyond_limit(deficit_government_setup):
    """Test that spending is blocked when it would exceed the debt/GDP limit."""
    government = deficit_government_setup
    government._assets = -2900  # Already near the debt limit
    target_agent = Mock()
    target_agent._assets = 0

    # Debt limit = 10000 * 0.30 = 3000
    # Current debt is 2900. Spending another 200 would make debt 3100, exceeding the limit.
    # Simulate FinanceSystem denying the bond issuance
    government.finance_system.issue_treasury_bonds.return_value = False

    amount_paid = government.provide_household_support(
        target_agent, 200, current_tick=1
    )

    assert amount_paid == 0
    assert government.assets == -2900  # Assets should not change
    assert target_agent.assets == 0

    # Finalize tick to update debt
    government.finalize_tick(1)
    assert government.total_debt == 2900
