from _typeshed import Incomplete
from modules.simulation.api import AgentSensorySnapshotDTO as AgentSensorySnapshotDTO
from simulation.dtos import GovernmentSensoryDTO as GovernmentSensoryDTO
from simulation.systems.api import ISensorySystem as ISensorySystem, SensoryContext as SensoryContext
from typing import Any, Deque

class SensorySystem(ISensorySystem):
    """
    Processes raw economic data into SMA buffers and produces Sensory DTOs.
    Owning the state of buffers.
    """
    config: Incomplete
    inflation_buffer: Deque[float]
    unemployment_buffer: Deque[float]
    gdp_growth_buffer: Deque[float]
    wage_buffer: Deque[float]
    approval_buffer: Deque[float]
    last_avg_price_for_sma: float
    last_gdp_for_sma: float
    def __init__(self, config: Any) -> None: ...
    def generate_government_sensory_dto(self, context: SensoryContext) -> GovernmentSensoryDTO:
        """
        Calculates indicators, updates buffers, and returns the DTO.
        """
