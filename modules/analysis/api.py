from __future__ import annotations
from typing import TypedDict, Dict, List, Protocol, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from modules.simulation.api import ISimulationState

@dataclass
class CrisisDistributionDTO:
    """DTO for firm crisis status distribution."""
    safe: int
    gray: int
    distress: int
    active: int

# --- Existing Verification DTOs (Keep for backward compatibility if needed) ---

class VerificationConfigDTO(TypedDict):
    """Configuration for the verification component."""
    max_starvation_rate: float
    max_debt_to_gdp: float
    zlb_threshold: float
    deficit_spending_threshold: float
    basic_food_key: str
    starvation_threshold: float
    # TBD: Define volatility reduction target

class StormReportDTO(TypedDict):
    """The final report summarizing the stress test results."""
    zlb_hit: bool
    deficit_spending_triggered: bool
    starvation_rate: float
    peak_debt_to_gdp: float
    volatility_metrics: Dict[str, float]
    success: bool

# --- New Phenomena Reporting DTOs ---

class PhenomenonEventDTO(TypedDict):
    """Generic representation of a detected economic event."""
    detector_name: str
    start_tick: int
    end_tick: int
    severity: float  # Normalized 0.0 to 1.0
    message: str
    details: Dict

class ResilienceIndexDTO(TypedDict):
    """Components of the calculated Resilience Index."""
    final_score: float # Score from 0 (brittle) to 100 (resilient)
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
    detected_events: List[PhenomenonEventDTO]
    key_timeseries: Dict[str, List[float]] # For plotting GDP, inflation, etc.

# --- Configuration DTOs ---

class DetectorConfigDTO(TypedDict):
    """Configuration for a single detector."""
    module: str # e.g., 'modules.analysis.detectors.LiquidityCrisisDetector'
    enabled: bool
    thresholds: Dict[str, float]

class AnalysisConfigDTO(TypedDict):
    """Top-level configuration for the PhenomenaAnalyzer."""
    detectors: Dict[str, DetectorConfigDTO]
    resilience_weights: Dict[str, float]

# --- Interfaces (Protocols) ---

class IDetector(Protocol):
    """Interface for a modular phenomenon detector."""
    def update(self, tick: int, sim_state: ISimulationState) -> None:
        """Update detector with data from the current tick."""
        ...

    def analyze(self) -> List[PhenomenonEventDTO]:
        """Analyze collected data and return detected events."""
        ...

class IAnalyzer(Protocol):
    """Interface for the main phenomena analyzer."""
    def run_tick(self, tick: int, sim_state: ISimulationState) -> None:
        ...

    def generate_report(self) -> PhenomenaReportDTO:
        ...
