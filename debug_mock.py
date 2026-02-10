from unittest.mock import MagicMock
from simulation.core_agents import Household

h = MagicMock(spec=Household)
h._econ_state = MagicMock()
h._econ_state.assets = 1000

print(f"assets type: {type(h._econ_state.assets)}")
print(f"assets value: {h._econ_state.assets}")
try:
    print(f"assets.get: {h._econ_state.assets.get}")
except AttributeError:
    print("AttributeError: assets has no get")
