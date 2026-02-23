import pytest
from unittest.mock import MagicMock
from modules.finance.monetary.api import (
    MacroEconomicSnapshotDTO, MonetaryPolicyConfigDTO, MonetaryRuleType, OMOActionType
)
from modules.finance.monetary.strategies import (
    TaylorRuleStrategy, FriedmanKPercentStrategy, McCallumRuleStrategy
)

@pytest.fixture
def snapshot():
    return MacroEconomicSnapshotDTO(
        tick=100,
        inflation_rate_annual=0.03, # 3%
        nominal_gdp=10_000_000,
        real_gdp_growth=0.02,
        unemployment_rate=0.06, # 6%
        current_m2_supply=1_000_000,
        current_monetary_base=200_000,
        velocity_of_money=10.0,
        output_gap=-0.01 # -1%
    )

@pytest.fixture
def config():
    return MonetaryPolicyConfigDTO(
        rule_type=MonetaryRuleType.TAYLOR_RULE,
        inflation_target=0.02,
        unemployment_target=0.05,
        taylor_alpha=1.5,
        taylor_beta=0.5,
        neutral_rate=0.02,
        m2_growth_target=0.05,
        ngdp_target_growth=0.04
    )

def test_taylor_rule(snapshot, config):
    strategy = TaylorRuleStrategy()
    current_rate = 0.04

    decision = strategy.calculate_decision(snapshot, current_rate, config)

    assert decision.rule_type == MonetaryRuleType.TAYLOR_RULE
    # i = r* + pi + alpha(pi - pi*) + beta(output_gap)
    # i = 0.02 + 0.03 + 1.5(0.03 - 0.02) + 0.5(-0.01)
    # i = 0.05 + 1.5(0.01) + 0.5(-0.01)
    # i = 0.05 + 0.015 - 0.005
    # i = 0.06

    # Delta = 0.06 - 0.04 = 0.02. Max change is 0.0025.
    # So should return 0.04 + 0.0025 = 0.0425
    expected_rate = 0.04 + 0.0025

    assert decision.target_interest_rate == pytest.approx(expected_rate)
    assert decision.omo_action == OMOActionType.NONE

def test_taylor_rule_no_explicit_output_gap(snapshot, config):
    # Snapshot without explicit output_gap (fallback to Okun's)
    snapshot_no_gap = MacroEconomicSnapshotDTO(
        tick=100,
        inflation_rate_annual=0.03,
        nominal_gdp=10_000_000,
        real_gdp_growth=0.02,
        unemployment_rate=0.06,
        current_m2_supply=1_000_000,
        current_monetary_base=200_000,
        velocity_of_money=10.0,
        output_gap=None
    )

    strategy = TaylorRuleStrategy()
    current_rate = 0.04
    decision = strategy.calculate_decision(snapshot_no_gap, current_rate, config)

    # Okun's Gap = u* - u = 0.05 - 0.06 = -0.01.
    # Same as previous test case.
    expected_rate = 0.04 + 0.0025
    assert decision.target_interest_rate == pytest.approx(expected_rate)

def test_friedman_rule(snapshot, config):
    strategy = FriedmanKPercentStrategy()
    current_rate = 0.04

    decision = strategy.calculate_decision(snapshot, current_rate, config)

    assert decision.rule_type == MonetaryRuleType.FRIEDMAN_K_PERCENT
    # Target M2 = 1_000_000 * 1.05 = 1_050_000
    # Delta = 50_000 (Positive)
    # Should BUY BONDS

    assert decision.target_m2_supply == 1_050_000
    assert decision.omo_action == OMOActionType.BUY_BONDS
    assert decision.omo_amount_pennies == 50_000
    assert decision.target_interest_rate == current_rate

def test_mccallum_rule(snapshot, config):
    strategy = McCallumRuleStrategy()
    current_rate = 0.04

    decision = strategy.calculate_decision(snapshot, current_rate, config)

    assert decision.rule_type == MonetaryRuleType.MCCALLUM_RULE
    # Target MB = Current MB * (1 + NGDP Growth Target)
    # MB = 200_000. NGDP Target Growth = 0.04.
    # Target MB = 200_000 * 1.04 = 208_000
    # Delta = 8_000

    assert decision.target_monetary_base == 208_000
    assert decision.omo_action == OMOActionType.BUY_BONDS
    assert decision.omo_amount_pennies == 8_000
