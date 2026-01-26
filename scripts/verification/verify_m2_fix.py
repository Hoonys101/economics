import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from simulation.world_state import WorldState
from simulation.agents.government import Government
from simulation.core_agents import Household
from unittest.mock import MagicMock
import logging

def test_m2_fix():
    logger = logging.getLogger("test")
    config = MagicMock()
    repo = MagicMock()

    state = WorldState(config, config, logger, repo)

    # Init Gov
    # Government now has assets included in M2.
    gov = Government(id=0, initial_assets=1000, config_module=config)
    state.government = gov

    # Init Household
    # Use a minimal Household setup
    hh = MagicMock(spec=Household)
    hh.id = 1
    hh.assets = 1000.0
    hh.is_active = True

    state.households.append(hh)

    # Check Initial M2
    # Should be Gov(1000) + HH(1000) = 2000
    m2_initial = state.calculate_total_money()
    print(f"Initial M2: {m2_initial}")

    # Verify my fix: Gov assets are included
    if m2_initial != 2000:
        print(f"FAILURE: Initial M2 is {m2_initial}, expected 2000. Did Government get included?")
    assert m2_initial == 2000

    # Simulate Transfer (e.g. Tax)
    amount = 500
    hh.assets -= amount
    gov._add_assets(amount)

    # Check Final M2
    m2_final = state.calculate_total_money()
    print(f"Final M2: {m2_final}")

    if m2_final != 2000:
        print(f"FAILURE: M2 changed to {m2_final} after transfer!")
    assert m2_final == 2000

    print("M2 Conservation Verified!")

if __name__ == "__main__":
    test_m2_fix()
