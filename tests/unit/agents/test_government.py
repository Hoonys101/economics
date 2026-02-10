import pytest
from unittest.mock import MagicMock, Mock, patch
from simulation.agents.government import Government
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def government_setup():
    # Mocking patches
    # TaxationSystem and FiscalPolicyManager are now inside TaxService.
    # We patch TaxService
    with patch('simulation.agents.government.TaxService') as mock_tax_service_cls, \
         patch('simulation.agents.government.MinistryOfEducation') as mock_education_ministry_cls, \
         patch('simulation.agents.government.WelfareManager') as mock_welfare_service_cls, \
         patch('simulation.agents.government.InfrastructureManager') as mock_infra_manager_cls:

        mock_tax_service_instance = mock_tax_service_cls.return_value
        mock_education_ministry_instance = mock_education_ministry_cls.return_value
        mock_welfare_service_instance = mock_welfare_service_cls.return_value
        mock_infra_manager_instance = mock_infra_manager_cls.return_value

        # Configure mock_tax_service defaults
        mock_tax_service_instance.get_revenue_this_tick.return_value = {}
        mock_tax_service_instance.get_total_collected_tax.return_value = {}
        mock_tax_service_instance.get_tax_revenue.return_value = {}
        mock_tax_service_instance.determine_fiscal_stance.return_value = Mock() # FiscalPolicyDTO
        mock_tax_service_instance.current_tick_stats = {"tax_revenue": {}, "total_collected": 0.0}

        mock_config = Mock()
        mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        mock_config.TICKS_PER_YEAR = 100
        mock_config.INCOME_TAX_RATE = 0.1 # This is the initial rate
        mock_config.CORPORATE_TAX_RATE = 0.2
        mock_config.TAX_MODE = "PROGRESSIVE"
        mock_config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        mock_config.TAX_BRACKETS = []
        mock_config.PUBLIC_EDU_BUDGET_RATIO = 0.2
        mock_config.SCHOLARSHIP_WEALTH_PERCENTILE = 0.2
        mock_config.EDUCATION_COST_PER_LEVEL = {1: 500}
        mock_config.SCHOLARSHIP_POTENTIAL_THRESHOLD = 0.7
        mock_config.ANNUAL_WEALTH_TAX_RATE = 0.02
        mock_config.WEALTH_TAX_THRESHOLD = 1000.0

        government = Government(id=1, initial_assets=100000, config_module=mock_config)
        # Mock settlement system
        government.settlement_system = Mock()

        # Manually set a different tax rate on the government instance to test that
        # the *current* rate is passed, not the initial config rate.
        government.income_tax_rate = 0.15
        government.corporate_tax_rate = 0.25

        yield {
            "government": government,
            "mock_tax_service": mock_tax_service_instance,
            "mock_education_ministry": mock_education_ministry_instance,
            "mock_welfare_service": mock_welfare_service_instance,
            "mock_infra_manager": mock_infra_manager_instance,
            "mock_config": mock_config
        }

def test_calculate_income_tax_delegation(government_setup):
    env = government_setup
    income = 50000
    survival_cost = 15000

    env["government"].calculate_income_tax(income, survival_cost)

    # Now delegates to TaxService
    env["mock_tax_service"].calculate_tax_liability.assert_called_once()
    # It passes self.fiscal_policy as first arg
    assert env["mock_tax_service"].calculate_tax_liability.call_args[0][0] == env["government"].fiscal_policy

def test_calculate_corporate_tax_delegation(government_setup):
    env = government_setup
    profit = 100000

    env["government"].calculate_corporate_tax(profit)

    env["mock_tax_service"].calculate_corporate_tax.assert_called_once_with(
        profit,
        env["government"].corporate_tax_rate # Should pass the current rate (0.25)
    )

def test_collect_tax_delegation(government_setup):
    """Test if collect_tax uses SettlementSystem and TaxService.record_revenue."""
    env = government_setup
    amount = 1000
    tax_type = 'income'
    source_id = 101
    current_tick = 50

    # Ensure settlement_system is present
    env["government"].settlement_system = Mock()
    env["government"].settlement_system.transfer.return_value = True

    env["government"].collect_tax(amount, tax_type, source_id, current_tick)

    # Note: Government.collect_tax calls settlement_system.transfer(payer, self, amount, memo)
    env["government"].settlement_system.transfer.assert_called_once_with(
        source_id,
        env["government"],
        amount,
        f"{tax_type} collection"
    )

    # And delegates recording to TaxService
    env["mock_tax_service"].record_revenue.assert_called_once()
    assert env["mock_tax_service"].record_revenue.call_args[0][0]['amount_collected'] == amount

def test_run_public_education_delegation(government_setup):
    """Test if run_public_education delegates to MinistryOfEducation."""
    env = government_setup
    mock_agent1 = Mock()
    mock_agent1.education_level = 1
    agents = [mock_agent1]

    env["government"].run_public_education(agents, env["mock_config"], 100)

    env["mock_education_ministry"].run_public_education.assert_called_once()


@pytest.fixture
def deficit_government_setup():
    mock_config = Mock()
    mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    mock_config.TICKS_PER_YEAR = 100
    mock_config.DEFICIT_SPENDING_ENABLED = True
    mock_config.DEFICIT_SPENDING_LIMIT_RATIO = 0.30
    mock_config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    mock_config.TAX_BRACKETS = []
    mock_config.ANNUAL_WEALTH_TAX_RATE = 0.02
    mock_config.WEALTH_TAX_THRESHOLD = 50000.0

    # Use Real WelfareService, Patch others
    with patch('simulation.agents.government.TaxService'), \
         patch('simulation.agents.government.MinistryOfEducation'), \
         patch('simulation.agents.government.InfrastructureManager'):

        government = Government(id=1, initial_assets=1000, config_module=mock_config)

        # Mock sensory data for GDP
        mock_sensory_data = Mock()
        mock_sensory_data.current_gdp = 10000
        government.sensory_data = mock_sensory_data

        # Mock FinanceSystem
        mock_finance = Mock()
        government.finance_system = mock_finance

        # Mock settlement system to handle transfer
        government.settlement_system = Mock()

        yield government

def test_deficit_spending_allowed_within_limit(deficit_government_setup):
    """Test that the government can spend more than its assets, creating debt."""
    government = deficit_government_setup

    # Setup for WelfareService logic
    government.welfare_budget_multiplier = 1.0

    # Asset is 1000. Request 500. No bonds needed.
    # We want to force bonds.
    # Set assets (Wallet) to low.
    government.wallet._balances[DEFAULT_CURRENCY] = 100.0

    mock_finance = government.finance_system

    def issue_bonds_side_effect(amount, tick):
        government.wallet.add(amount, DEFAULT_CURRENCY)
        return (["bond"], [Mock(transaction_type='bond_issuance')])

    mock_finance.issue_treasury_bonds.side_effect = issue_bonds_side_effect

    target_agent = Mock()
    target_agent.id = "target_1"

    txs = government.provide_household_support(target_agent, 500, current_tick=1)

    # Needed 400. Bonds issued.
    # Should have welfare tx (500) and bond txs.
    assert len(txs) >= 1
    welfare_tx = [tx for tx in txs if tx.transaction_type == 'welfare'][0]
    assert welfare_tx.price == 500

    # Verify bond issuance requested
    mock_finance.issue_treasury_bonds.assert_called()

def test_deficit_spending_blocked_beyond_limit(deficit_government_setup):
    """Test that spending is blocked when it would exceed the debt/GDP limit."""
    government = deficit_government_setup
    government.wallet._balances[DEFAULT_CURRENCY] = 100.0
    target_agent = Mock()
    target_agent.id = "target_1"

    # Simulate FinanceSystem denying the bond issuance
    government.finance_system.issue_treasury_bonds.return_value = (None, [])
    
    txs = government.provide_household_support(target_agent, 500, current_tick=1)

    # Should return empty list because bond failed
    assert len(txs) == 0
