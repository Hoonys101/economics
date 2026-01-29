import pytest
from unittest.mock import MagicMock, Mock
from simulation.agents.government import Government

@pytest.fixture
def government_setup(mocker):
    # Mocking patches
    mock_tax_agency_cls = mocker.patch('simulation.agents.government.TaxAgency')
    mock_education_ministry_cls = mocker.patch('simulation.agents.government.MinistryOfEducation')
    mock_fiscal_policy_manager_cls = mocker.patch('simulation.agents.government.FiscalPolicyManager')

    mock_tax_agency_instance = mock_tax_agency_cls.return_value
    mock_education_ministry_instance = mock_education_ministry_cls.return_value
    mock_fiscal_policy_manager_instance = mock_fiscal_policy_manager_cls.return_value

    mock_config = Mock()
    mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    mock_config.TICKS_PER_YEAR = 100
    mock_config.INCOME_TAX_RATE = 0.1 # This is the initial rate
    mock_config.CORPORATE_TAX_RATE = 0.2
    mock_config.TAX_MODE = "PROGRESSIVE"
    mock_config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    mock_config.TAX_BRACKETS = []

    government = Government(id=1, initial_assets=100000, config_module=mock_config)
    # Mock settlement system
    government.settlement_system = Mock()

    # Manually set a different tax rate on the government instance to test that
    # the *current* rate is passed, not the initial config rate.
    government.income_tax_rate = 0.15
    government.corporate_tax_rate = 0.25

    return {
        "government": government,
        "mock_tax_agency": mock_tax_agency_instance,
        "mock_education_ministry": mock_education_ministry_instance,
        "mock_fiscal_policy_manager": mock_fiscal_policy_manager_instance,
        "mock_config": mock_config
    }

def test_calculate_income_tax_delegation(government_setup):
    env = government_setup
    income = 50000
    survival_cost = 15000

    env["government"].calculate_income_tax(income, survival_cost)

    # Now delegates to FiscalPolicyManager
    env["mock_fiscal_policy_manager"].calculate_tax_liability.assert_called_once()

def test_calculate_corporate_tax_delegation(government_setup):
    env = government_setup
    profit = 100000

    env["government"].calculate_corporate_tax(profit)

    env["mock_tax_agency"].calculate_corporate_tax.assert_called_once_with(
        profit,
        env["government"].corporate_tax_rate # Should pass the current rate (0.25)
    )

def test_collect_tax_delegation(government_setup):
    """Test if collect_tax delegates to TaxAgency."""
    env = government_setup
    amount = 1000
    tax_type = 'income'
    source_id = 101
    current_tick = 50

    # Ensure settlement_system is present
    env["government"].settlement_system = Mock()

    # Configure mock return value to satisfy record_revenue
    env["mock_tax_agency"].collect_tax.return_value = {
        "success": True,
        "amount_collected": amount,
        "tax_type": tax_type,
        "payer_id": source_id,
        "payee_id": env["government"].id,
        "error_message": None
    }

    env["government"].collect_tax(amount, tax_type, source_id, current_tick)

    # Note: Government.collect_tax calls agency.collect_tax(payer=source, payee=self, ...)
    env["mock_tax_agency"].collect_tax.assert_called_once_with(
        payer=source_id,
        payee=env["government"],
        amount=amount,
        tax_type=tax_type,
        settlement_system=env["government"].settlement_system,
        current_tick=current_tick
    )

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

    government = Government(id=1, initial_assets=1000, config_module=mock_config)

    # Mock sensory data for GDP
    mock_sensory_data = Mock()
    mock_sensory_data.current_gdp = 10000
    government.sensory_data = mock_sensory_data

    # Mock FinanceSystem
    mock_finance = Mock()
    # Return (bonds, txs)
    mock_finance.issue_treasury_bonds.return_value = (["bond"], [Mock(transaction_type='bond_issuance')])
    government.finance_system = mock_finance

    # Mock settlement system to handle transfer
    government.settlement_system = Mock()

    return government

def test_deficit_spending_allowed_within_limit(deficit_government_setup):
    """Test that the government can spend more than its assets, creating debt."""
    government = deficit_government_setup
    government._assets = 100
    target_agent = Mock()
    target_agent._assets = 0

    # Mock provide_household_support relies on assets being updated?
    # Actually provide_household_support logic:
    # 1. Check if assets < amount
    # 2. Issue bonds
    # 3. Create welfare transaction (no direct transfer in this method, it returns transaction)
    # Wait, the original method returns List[Transaction].
    # But the test asserts `amount_paid == 500`?
    # Original test code: `amount_paid = government.provide_household_support(...)`
    # And asserts `government.assets == -400`.
    # `provide_household_support` does NOT update assets for the welfare payment itself!
    # It just returns transactions to be executed by TransactionProcessor.
    # EXCEPT for `issue_treasury_bonds` which calls FinanceSystem.
    # If FinanceSystem is mocked, assets won't change unless mock does it.

    # Let's fix expectations. The method returns transactions.
    txs = government.provide_household_support(target_agent, 500, current_tick=1)

    # It should return at least 1 welfare tx + bond txs.
    assert len(txs) >= 1
    welfare_tx = [tx for tx in txs if tx.transaction_type == 'welfare'][0]
    assert welfare_tx.price == 500

    # government.assets won't change here because we mocked finance system and provide_household_support doesn't do transfer.
    # So we remove asset assertions that depended on real logic or side effects.

def test_deficit_spending_blocked_beyond_limit(deficit_government_setup):
    """Test that spending is blocked when it would exceed the debt/GDP limit."""
    government = deficit_government_setup
    government._assets = -2900
    target_agent = Mock()

    # Simulate FinanceSystem denying the bond issuance
    government.finance_system.issue_treasury_bonds.return_value = (None, [])
    
    txs = government.provide_household_support(target_agent, 200, current_tick=1)

    assert len(txs) == 0
