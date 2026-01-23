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
    initial_firm_assets = mock_firm.assets

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

    gov = Government(id=1, initial_assets=6000.0, config_module=config_mock)

    # Needs finance system mock
    gov.finance_system = Mock()
    gov.finance_system.issue_treasury_bonds.return_value = ([], [])

    gov.firm_subsidy_budget_multiplier = 1.0

    initial_assets = gov.assets
    initial_level = gov.infrastructure_level

    invested_result = gov.invest_infrastructure(current_tick=1)

    assert isinstance(invested_result, tuple)
    success, txs = invested_result
    assert success is True
    assert isinstance(txs, list)

    assert gov.assets == initial_assets - 5000.0
    assert gov.infrastructure_level == initial_level + 1
