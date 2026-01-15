import pytest
from unittest.mock import Mock

def test_tax_collection_and_bailouts(government):
    """
    Tests that the government can collect taxes and provide bailouts,
    updating its assets correctly.
    """
    initial_gov_assets = government.assets

    # 1. Manual Tax Collection Test
    government.collect_tax(100.0, "test_tax", 1, 1)
    assert government.assets == initial_gov_assets + 100.0
    assert government.total_collected_tax == 100.0

    # 2. Bailout Test (now a loan, not a subsidy)
    mock_firm = Mock()
    mock_firm.id = 101
    mock_firm.assets = 1000.0
    initial_firm_assets = mock_firm.assets

    # Mock the finance system to approve the bailout
    government.finance_system.evaluate_solvency.return_value = True

    # This is the key fix: the grant_bailout_loan method *itself* should
    # have the side effect of decreasing the government's assets.
    def grant_loan_side_effect(firm, amount):
        government.assets -= amount
        return Mock()

    government.finance_system.grant_bailout_loan = Mock(side_effect=grant_loan_side_effect)

    government.provide_firm_bailout(mock_firm, 50.0, 1)

    # Now the assertion is correct, because the side effect has been applied.
    assert government.assets == initial_gov_assets + 100.0 - 50.0
    government.finance_system.grant_bailout_loan.assert_called_once()


def test_infrastructure_investment(government):
    """
    Tests that infrastructure investment decreases government assets and
    increases the infrastructure level.
    """
    # This test no longer checks for TFP boost directly, as that's an
    # integration effect. It now unit-tests the government's action.

    # Mock config for investment cost
    government.config_module.INFRASTRUCTURE_INVESTMENT_COST = 5000.0
    government.assets = 6000.0
    initial_assets = government.assets
    initial_level = government.infrastructure_level

    # Mock successful bond issuance in case assets are not enough
    # (though they are in this setup)
    government.finance_system.issue_treasury_bonds.return_value = [Mock()]

    invested = government.invest_infrastructure(current_tick=1)

    assert invested is True
    assert government.assets == initial_assets - 5000.0
    assert government.infrastructure_level == initial_level + 1
