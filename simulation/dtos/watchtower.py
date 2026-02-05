from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class IntegrityDTO:
    m2_leak: float
    fps: float

@dataclass
class MacroDTO:
    gdp: float
    cpi: float
    unemploy: float
    gini: float

@dataclass
class FinanceRatesDTO:
    base: float
    call: float
    loan: float
    savings: float

@dataclass
class FinanceSupplyDTO:
    m0: float
    m1: float
    m2: float
    velocity: float

@dataclass
class FinanceDTO:
    rates: FinanceRatesDTO
    supply: FinanceSupplyDTO

@dataclass
class PoliticsApprovalDTO:
    total: float
    low: float
    mid: float
    high: float

@dataclass
class PoliticsStatusDTO:
    ruling_party: str
    cohesion: float

@dataclass
class PoliticsFiscalDTO:
    revenue: float
    welfare: float
    debt: float

@dataclass
class PoliticsDTO:
    approval: PoliticsApprovalDTO
    status: PoliticsStatusDTO
    fiscal: PoliticsFiscalDTO

@dataclass
class PopulationDistributionDTO:
    q1: float
    q2: float
    q3: float
    q4: float
    q5: float

@dataclass
class PopulationMetricsDTO:
    birth: float
    death: float

@dataclass
class PopulationDTO:
    distribution: PopulationDistributionDTO
    active_count: int
    metrics: PopulationMetricsDTO

@dataclass
class WatchtowerSnapshotDTO:
    tick: int
    status: str
    integrity: IntegrityDTO
    macro: MacroDTO
    finance: FinanceDTO
    politics: PoliticsDTO
    population: PopulationDTO
