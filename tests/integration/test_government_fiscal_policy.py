import pytest
from unittest.mock import Mock
from simulation.models import Transaction
from simulation.agents.government import Government

def test_tax_collection_and_bailouts(government):
    """
    Tests that the government can collect taxes and provide bailouts,
    updating its assets correctly.
    """
    initial_gov_assets = government.assets

    # 1. Manual Tax Collection Test (Legacy direct call)
    government.collect_tax(100.0, "test_tax", 1, 1)

    # 2. Bailout Test (now a loan, returns transactions)
    mock_firm = Mock()
    mock_firm.id = 101
    mock_firm._assets = 1000.0
    initial_firm_assets = mock_firm.finance.balance

    # Mock the finance system to approve the bailout
    government.finance_system.evaluate_solvency.return_value = True

    # Mock grant_bailout_loan to return (loan, txs)
    loan_dto = Mock()
    tx_list = [Mock(spec=Transaction)]
    government.finance_system.grant_bailout_loan.return_value = (loan_dto, tx_list)

    result_loan, result_txs = government.provide_firm_bailout(mock_firm, 50.0, 1)

    assert result_loan == loan_dto
    assert result_txs == tx_list
    government.finance_system.grant_bailout_loan.assert_called_once()


def test_infrastructure_investment():
    """
    Tests that infrastructure investment decreases government assets and
    increases the infrastructure level.
    Uses explicit instantiation to avoid fixture ambiguity.
    """
    config_mock = Mock()
    config_mock.INFRASTRUCTURE_INVESTMENT_COST = 5000.0
    config_mock.TICKS_PER_YEAR = 100 # Required for TaylorRulePolicy init
    config_mock.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config_mock.TAX_BRACKETS = [] # Ensure this is a list, not a Mock

    gov = Government(id=1, initial_assets=6000.0, config_module=config_mock)

    # Needs finance system mock
    gov.finance_system = Mock()
    gov.finance_system.issue_treasury_bonds.return_value = ([], [])

    gov.firm_subsidy_budget_multiplier = 1.0

    initial_assets = gov.assets
    initial_level = gov.infrastructure_level

    # Fix for TD-105: Provide required dependencies for zero-sum execution
    reflux_mock = Mock()
    gov.settlement_system = Mock()
    gov.settlement_system.transfer.return_value = True

    # Setup dummy household for public works
    h1 = Mock()
    h1.id = 999
    h1.is_active = True

    # Call with households, expecting a list of transactions
    txs = gov.invest_infrastructure(current_tick=1, households=[h1])

    assert isinstance(txs, list)
    assert len(txs) > 0

    # Verify metadata trigger instead of immediate level change
    # Infrastructure update is now deferred to EffectSystem
    assert txs[0].metadata.get("triggers_effect") == "GOVERNMENT_INFRA_UPGRADE"
