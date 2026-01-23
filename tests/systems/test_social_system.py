import pytest
from unittest.mock import MagicMock
from simulation.systems.social_system import SocialSystem
from simulation.systems.api import SocialMobilityContext


class MockHousehold:
    def __init__(self, id, consumption, housing_tier, is_active=True):
        self.id = id
        self.current_consumption = consumption
        self.housing_tier = housing_tier  # Helper for mocking HousingManager
        self.is_active = is_active
        self.social_rank = 0.0


class MockHousingManager:
    def __init__(self, agent, config):
        pass

    def get_housing_tier(self, agent):
        return agent.housing_tier


@pytest.fixture
def social_system():
    config = MagicMock()
    return SocialSystem(config)


def test_update_social_ranks(social_system):
    # Setup
    h1 = MockHousehold(
        1, consumption=100, housing_tier=1.0
    )  # Score = 1000 + 1000 = 2000
    h2 = MockHousehold(
        2, consumption=200, housing_tier=3.0
    )  # Score = 2000 + 3000 = 5000 (Top)
    h3 = MockHousehold(
        3, consumption=50, housing_tier=1.0
    )  # Score = 500 + 1000 = 1500 (Bottom)

    households = [h1, h2, h3]
    context: SocialMobilityContext = {
        "households": households,
        "housing_manager": MockHousingManager(None, None),
    }

    # Execute
    social_system.update_social_ranks(context)

    # Verify
    # h2 should be Rank 0 -> Percentile 1.0
    # h1 should be Rank 1 -> Percentile 1 - 1/3 = 0.66
    # h3 should be Rank 2 -> Percentile 1 - 2/3 = 0.33

    assert h2.social_rank == 1.0
    assert abs(h1.social_rank - (1.0 - 1 / 3)) < 0.01
    assert abs(h3.social_rank - (1.0 - 2 / 3)) < 0.01


def test_calculate_reference_standard(social_system):
    # Setup
    # Top 20% of 5 agents = 1 agent
    h1 = MockHousehold(1, consumption=100, housing_tier=1.0)  # Rank 1.0 (Assume sorted)
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
        "households": households,
        "housing_manager": MockHousingManager(None, None),
    }

    # Execute
    std = social_system.calculate_reference_standard(context)

    # Verify
    # Top 1 is h1.
    assert std["avg_consumption"] == 100.0
    assert std["avg_housing_tier"] == 1.0
