from dataclasses import dataclass, field
from typing import Dict, List, Literal

@dataclass
class SystemIntegrityDTO:
    m2_leak: float
    fps: float

@dataclass
class MacroEconomyDTO:
    gdp_growth: float
    inflation_rate: float
    unemployment_rate: float
    gini_coefficient: float

@dataclass
class MonetaryDTO:
    base_rate: float
    interbank_rate: float
    m2_supply: float
    exchange_rates: Dict[str, float]

@dataclass
class PoliticsDTO:
    party: str # 'RED' | 'BLUE' | 'NEUTRAL'
    approval_rating: float
    social_cohesion: float
    current_events: List[str]

@dataclass
class DashboardSnapshotDTO:
    """The root DTO for The Watchtower dashboard, sent via WebSocket."""
    tick: int
    timestamp: str # ISO-8601
    system_integrity: SystemIntegrityDTO
    macro_economy: MacroEconomyDTO
    monetary: MonetaryDTO
    politics: PoliticsDTO
