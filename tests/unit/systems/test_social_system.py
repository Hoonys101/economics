import pytest
from unittest.mock import MagicMock
from simulation.systems.social_system import SocialSystem
from simulation.systems.api import SocialMobilityContext

class MockHousehold:
    def __init__(self, id, consumption, housing_tier, is_active=True):
        self.id = id
        self.current_consumption = consumption
        self.housing_tier = housing_tier
        # Map housing_tier to residing_property_id (Tier > 0 -> has house)
        # Note: HousingManager allowed tiers > 1.0 (based on logic).
        # The new SocialSystem simple logic treats any house as 1.0.
        # So we adjust expectations or inputs.
        # For this test, h2 had tier 3.0. This implies legacy logic allowed value-based tiers.
        # But SocialSystem now returns 1.0 for any house.
        # So we need to update the test expectation or inputs.
        # If we want to test correct ranking, we should ensure consumption dominates or tiers match new logic.
        # Let's adjust inputs to match the new simple 0/1 logic.

        self.residing_property_id = 1 if housing_tier > 0 else None
        self._econ_state = MagicMock()
        self._econ_state.current_consumption = consumption
        self._econ_state.residing_property_id = self.residing_property_id

        self.is_active = is_active
        self.social_rank = 0.0

@pytest.fixture
def social_system():
    config = MagicMock()
    return SocialSystem(config)

def test_update_social_ranks(social_system):
    # Setup
    # Updated logic: Housing Tier is 1.0 if owning/residing, else 0.0.
    # Scores: Consumption * 10 + Tier * 1000

    # h2: Cons 200 -> Score 2000. Tier 1 -> Score 1000. Total 3000.
    h2 = MockHousehold(2, consumption=200, housing_tier=1.0)

    # h1: Cons 100 -> Score 1000. Tier 1 -> Score 1000. Total 2000.
    h1 = MockHousehold(1, consumption=100, housing_tier=1.0)

    # h3: Cons 50 -> Score 500. Tier 1 -> Score 1000. Total 1500.
    h3 = MockHousehold(3, consumption=50, housing_tier=1.0)

    households = [h1, h2, h3]
    context: SocialMobilityContext = {
        "households": households
    }

    # Execute
    social_system.update_social_ranks(context)

    # Verify
    # h2 should be Rank 0 -> Percentile 1.0
    # h1 should be Rank 1 -> Percentile 1 - 1/3 = 0.66
    # h3 should be Rank 2 -> Percentile 1 - 2/3 = 0.33

    assert h2.social_rank == 1.0
    assert abs(h1.social_rank - (1.0 - 1/3)) < 0.01
    assert abs(h3.social_rank - (1.0 - 2/3)) < 0.01

def test_calculate_reference_standard(social_system):
    # Setup
    # Top 20% of 5 agents = 1 agent
    h1 = MockHousehold(1, consumption=100, housing_tier=1.0) # Rank 1.0 (Assume sorted)
    h1.social_rank = 1.0
    h2 = MockHousehold(2, consumption=50, housing_tier=1.0)
    h2.social_rank = 0.8
    h3 = MockHousehold(3, consumption=10, housing_tier=1.0)
    h3.social_rank = 0.6
    h4 = MockHousehold(4, consumption=10, housing_tier=1.0)
    h4.social_rank = 0.4
    h5 = MockHousehold(5, consumption=10, housing_tier=1.0)
    h5.social_rank = 0.2

    households = [h1, h2, h3, h4, h5]
    context: SocialMobilityContext = {
        "households": households
    }

    # Execute
    std = social_system.calculate_reference_standard(context)

    # Verify
    # Top 1 is h1.
    assert std["avg_consumption"] == 100.0
    assert std["avg_housing_tier"] == 1.0
