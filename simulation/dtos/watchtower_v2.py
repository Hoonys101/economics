from dataclasses import dataclass
from typing import Dict, Any, Optional
from simulation.dtos.watchtower import (
    IntegrityDTO, MacroDTO, FinanceDTO, PoliticsDTO, PopulationDTO
)

@dataclass
class WatchtowerV2DTO:
    """
    Watchtower V2 Data Transfer Object.
    Aggregates simulation state snapshots for the UI.
    """
    tick: int
    timestamp: float
    status: str
    integrity: IntegrityDTO
    macro: MacroDTO
    finance: FinanceDTO
    politics: PoliticsDTO
    population: PopulationDTO
