from dataclasses import dataclass, field
from modules.analysis.scenario_verifier.api import ScenarioReportDTO as ScenarioReportDTO
from simulation.dtos.watchtower import FinanceDTO as FinanceDTO, IntegrityDTO as IntegrityDTO, MacroDTO as MacroDTO, PoliticsDTO as PoliticsDTO, PopulationDTO as PopulationDTO
from typing import Any

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
    scenario_reports: list[ScenarioReportDTO] = field(default_factory=list)
    custom_data: dict[str, Any] = field(default_factory=dict)
