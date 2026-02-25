from _typeshed import Incomplete
from modules.common.config.impl import ConfigManagerImpl as ConfigManagerImpl
from modules.simulation.api import AgentCoreConfigDTO as AgentCoreConfigDTO, AgentStateDTO as AgentStateDTO
from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO, HouseholdConfigDTO as HouseholdConfigDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.engine import Simulation as Simulation
from typing import Any

logger: Incomplete

def create_simulation(overrides: dict[str, Any] = None) -> Simulation:
    """Create simulation instance with optional config overrides."""
