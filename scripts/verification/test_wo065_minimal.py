import math
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from simulation.agents.government import Government
import config
from unittest.mock import Mock

gov = Government(id=999, initial_assets=0.0, config_module=config)
gov.finance_system = Mock()
gov.sensory_data = Mock()
gov.total_money_destroyed += 1000.0
assert math.isclose(gov.total_money_destroyed, 1000.0)
print('PASS')
