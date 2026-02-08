from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.models import Talent
from simulation.ai.api import Personality
from modules.simulation.api import AgentCoreConfigDTO

def test_household_instantiation():
    core_config = AgentCoreConfigDTO(
        id=1, name="HH", logger=MagicMock(), memory_interface=None, value_orientation="neutral", initial_needs={}
    )
    config = MagicMock()
    config.initial_household_age_range = (20, 30) # Fix
    config.price_memory_length = 10
    config.wage_memory_length = 10
    config.ticks_per_year = 100
    config.initial_aptitude_distribution = (0.5, 0.1)
    config.conformity_ranges = {}
    config.initial_household_assets_mean = 1000.0
    config.quality_pref_snob_min = 0.8
    config.quality_pref_miser_max = 0.2
    config.adaptation_rate_normal = 0.1
    config.value_orientation_mapping = {}

    try:
        h = Household(
            core_config=core_config,
            engine=MagicMock(),
            talent=Talent(0.1, 1.0),
            goods_data=[],
            personality=Personality.BALANCED,
            config_dto=config
        )
        print("Household instantiated successfully")
    except Exception as e:
        print(f"Instantiation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_household_instantiation()
