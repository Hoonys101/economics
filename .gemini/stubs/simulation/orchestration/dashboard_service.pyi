from _typeshed import Incomplete
from simulation.dtos.watchtower import FinanceDTO as FinanceDTO, FinanceRatesDTO as FinanceRatesDTO, FinanceSupplyDTO as FinanceSupplyDTO, IntegrityDTO as IntegrityDTO, MacroDTO as MacroDTO, PoliticsApprovalDTO as PoliticsApprovalDTO, PoliticsDTO as PoliticsDTO, PoliticsFiscalDTO as PoliticsFiscalDTO, PoliticsStatusDTO as PoliticsStatusDTO, PopulationDTO as PopulationDTO, PopulationDistributionDTO as PopulationDistributionDTO, PopulationMetricsDTO as PopulationMetricsDTO, WatchtowerSnapshotDTO as WatchtowerSnapshotDTO
from simulation.engine import Simulation as Simulation
from simulation.orchestration.persistence_bridge import PersistenceBridge as PersistenceBridge
from typing import Any

logger: Incomplete

class DashboardService:
    state: Incomplete
    simulation: Incomplete
    persistence: Incomplete
    def __init__(self, simulation_or_state: Simulation | Any) -> None:
        """
        Accepts Simulation OR WorldState to allow decoupled usage (e.g., inside Phase 8).
        """
    def get_snapshot(self) -> WatchtowerSnapshotDTO: ...
