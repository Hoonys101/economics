import pytest
from config import defaults

def test_config_constants_rebalancing():
    """
    Verify that constants have been updated according to WO-SPEC-CONFIG-SCALING.
    """
    # 2.1. Global Money Supply & Distribution
    assert defaults.INITIAL_MONEY_SUPPLY == 100_000_000
    assert defaults.INITIAL_HOUSEHOLD_ASSETS_MEAN == 200_000
    assert defaults.INITIAL_FIRM_CAPITAL_MEAN == 5_000_000

    # 2.2. Operational Thresholds
    assert defaults.STARTUP_COST == 1_000_000
    assert defaults.WEALTH_TAX_THRESHOLD == 10_000_000
    assert defaults.FIRM_MAINTENANCE_FEE == 10_000
    assert defaults.HOMELESS_PENALTY_PER_TICK == 1_000
    assert defaults.INFRASTRUCTURE_INVESTMENT_COST == 2_000_000

    # 2.3. New Configurable Constants
    assert defaults.FISCAL_TAX_RATE_MIN == 0.05
    assert defaults.FISCAL_TAX_RATE_MAX == 0.60
    assert defaults.FISCAL_TAX_ADJUSTMENT_STEP == 0.01
    assert defaults.DEBT_CEILING_HARD_LIMIT_RATIO == 1.5

def test_config_pennies_integrity():
    """
    Verify that monetary values are integers (Pennies).
    """
    assert isinstance(defaults.INITIAL_MONEY_SUPPLY, int)
    assert isinstance(defaults.INITIAL_HOUSEHOLD_ASSETS_MEAN, int)
    assert isinstance(defaults.INITIAL_FIRM_CAPITAL_MEAN, int)
    assert isinstance(defaults.STARTUP_COST, int)
    assert isinstance(defaults.WEALTH_TAX_THRESHOLD, int)
    assert isinstance(defaults.FIRM_MAINTENANCE_FEE, int)

    # Check fallback price
    assert defaults.DEFAULT_FALLBACK_PRICE == 1000
    assert isinstance(defaults.DEFAULT_FALLBACK_PRICE, int)
