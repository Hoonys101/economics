import pytest
from unittest.mock import Mock, MagicMock
from simulation.ai.enums import PoliticalParty, PolicyActionTag
from simulation.dtos.api import GovernmentSensoryDTO
from modules.government.policies.adaptive_gov_brain import AdaptiveGovBrain
from modules.government.dtos import PolicyActionDTO

@pytest.fixture
def mock_sensory_data():
    return GovernmentSensoryDTO(
        tick=100,
        inflation_sma=0.02,
        unemployment_sma=0.05,
        gdp_growth_sma=0.03,
        wage_sma=50.0,
        approval_sma=0.5,
        current_gdp=10000.0,
        gini_index=0.4,
        approval_low_asset=0.4,
        approval_high_asset=0.6
    )

def test_propose_actions_red_party(mock_sensory_data):
    brain = AdaptiveGovBrain(config=Mock())
    actions = brain.propose_actions(mock_sensory_data, PoliticalParty.RED)

    assert len(actions) > 0
    # Red Party favors actions that increase LowAssetApproval and Decrease Gini
    # e.g., Welfare Increase

    # Check if Welfare Increase is ranked high
    welfare_increase = next((a for a in actions if a.action_type == "ADJUST_WELFARE" and a.params.get("multiplier_delta", 0) > 0), None)
    assert welfare_increase is not None

    # Check utility calculation
    # Current Utility: 0.7*0.4 + 0.3*(1-0.4) = 0.28 + 0.18 = 0.46
    # Welfare Increase predicts: LowApproval += 0.05 -> 0.45. Gini -= 0.01 -> 0.39.
    # Predicted Utility: 0.7*0.45 + 0.3*(1-0.39) = 0.315 + 0.183 = 0.498

    # Allow some float precision margin
    assert welfare_increase.utility > 0.46

def test_propose_actions_blue_party(mock_sensory_data):
    brain = AdaptiveGovBrain(config=Mock())
    actions = brain.propose_actions(mock_sensory_data, PoliticalParty.BLUE)

    assert len(actions) > 0
    # Blue favors HighAssetApproval and GDP Growth

    # Check Tax Cut (Corp)
    corp_tax_cut = next((a for a in actions if a.action_type == "ADJUST_CORP_TAX" and a.params.get("rate_delta", 0) < 0), None)
    assert corp_tax_cut is not None

    # Current Utility: 0.6*0.6 + 0.4*0.03 = 0.36 + 0.012 = 0.372
    # Tax Cut predicts: HighApproval += 0.04 -> 0.64. GDP += 0.005 -> 0.035.
    # Predicted Utility: 0.6*0.64 + 0.4*0.035 = 0.384 + 0.014 = 0.398

    assert corp_tax_cut.utility > 0.372

def test_candidates_generation():
    brain = AdaptiveGovBrain(config=Mock())
    candidates = brain._generate_candidates()
    assert len(candidates) >= 6
    tags = {c.tag for c in candidates}
    assert PolicyActionTag.KEYNESIAN_FISCAL in tags
    assert PolicyActionTag.AUSTRIAN_AUSTERITY in tags
