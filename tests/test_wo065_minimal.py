import math
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulation.agents.government import Government
import config

gov = Government(id=999, initial_assets=0.0, config_module=config)
gov.total_money_destroyed += 1000.0
assert math.isclose(gov.total_money_destroyed, 1000.0)
print('PASS')
