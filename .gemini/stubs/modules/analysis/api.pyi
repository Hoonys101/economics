from dataclasses import dataclass
from modules.simulation.api import ISimulationState as ISimulationState
from typing import Protocol, TypedDict

@dataclass
class CrisisDistributionDTO:
    """DTO for firm crisis status distribution."""
    safe: int
    gray: int
    distress: int
    active: int

class VerificationConfigDTO(TypedDict):
    """Configuration for the verification component."""
    max_starvation_rate: float
    max_debt_to_gdp: float
    zlb_threshold: float
    deficit_spending_threshold: float
    basic_food_key: str
    starvation_threshold: float

class StormReportDTO(TypedDict):
    """The final report summarizing the stress test results."""
    zlb_hit: bool
    deficit_spending_triggered: bool
    starvation_rate: float
    peak_debt_to_gdp: float
    volatility_metrics: dict[str, float]
    success: bool

class PhenomenonEventDTO(TypedDict):
    """Generic representation of a detected economic event."""
    detector_name: str
    start_tick: int
    end_tick: int
    severity: float
    message: str
    details: dict

class ResilienceIndexDTO(TypedDict):
    """Components of the calculated Resilience Index."""
    final_score: float
    volatility_score: float
    recovery_score: float
    crisis_penalty: float
    policy_bonus: float

class PolicySynergyMetrics(TypedDict):
    """Metrics to analyze the interaction of policies."""
    fiscal_stabilizer_activations: int
    monetary_stabilizer_activations: int
    correlation_gdp_fiscal_stimulus: float
    zlb_duration: int

class PhenomenaReportDTO(TypedDict):
    """The final, comprehensive report object."""
    simulation_ticks: int
    resilience_index: ResilienceIndexDTO
    policy_metrics: PolicySynergyMetrics
    detected_events: list[PhenomenonEventDTO]
    key_timeseries: dict[str, list[float]]

class DetectorConfigDTO(TypedDict):
    """Configuration for a single detector."""
    module: str
    enabled: bool
    thresholds: dict[str, float]

class AnalysisConfigDTO(TypedDict):
    """Top-level configuration for the PhenomenaAnalyzer."""
    detectors: dict[str, DetectorConfigDTO]
    resilience_weights: dict[str, float]

class IDetector(Protocol):
    """Interface for a modular phenomenon detector."""
    def update(self, tick: int, sim_state: ISimulationState) -> None:
        """Update detector with data from the current tick."""
    def analyze(self) -> list[PhenomenonEventDTO]:
        """Analyze collected data and return detected events."""

class IAnalyzer(Protocol):
    """Interface for the main phenomena analyzer."""
    def run_tick(self, tick: int, sim_state: ISimulationState) -> None: ...
    def generate_report(self) -> PhenomenaReportDTO: ...
