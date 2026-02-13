from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from simulation.dtos.watchtower import (
    IntegrityDTO, MacroDTO, FinanceDTO, PoliticsDTO, PopulationDTO
)
from modules.analysis.scenario_verifier.api import ScenarioReportDTO

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
    scenario_reports: List[ScenarioReportDTO] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
