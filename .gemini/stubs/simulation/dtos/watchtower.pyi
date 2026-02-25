from pydantic import BaseModel, Field as Field

class IntegrityDTO(BaseModel):
    m2_leak: int
    fps: float

class MacroDTO(BaseModel):
    gdp: int
    cpi: float
    unemploy: float
    gini: float

class FinanceRatesDTO(BaseModel):
    base: float
    call: float
    loan: float
    savings: float

class FinanceSupplyDTO(BaseModel):
    m0: int
    m1: int
    m2: int
    velocity: float

class FinanceDTO(BaseModel):
    rates: FinanceRatesDTO
    supply: FinanceSupplyDTO

class PoliticsApprovalDTO(BaseModel):
    total: float
    low: float
    mid: float
    high: float

class PoliticsStatusDTO(BaseModel):
    ruling_party: str
    cohesion: float

class PoliticsFiscalDTO(BaseModel):
    revenue: int
    welfare: int
    debt: int

class PoliticsDTO(BaseModel):
    approval: PoliticsApprovalDTO
    status: PoliticsStatusDTO
    fiscal: PoliticsFiscalDTO

class PopulationDistributionDTO(BaseModel):
    q1: float
    q2: float
    q3: float
    q4: float
    q5: float

class PopulationMetricsDTO(BaseModel):
    birth: float
    death: float

class PopulationDTO(BaseModel):
    distribution: PopulationDistributionDTO
    active_count: int
    metrics: PopulationMetricsDTO

class WatchtowerSnapshotDTO(BaseModel):
    tick: int
    timestamp: float
    status: str
    integrity: IntegrityDTO
    macro: MacroDTO
    finance: FinanceDTO
    politics: PoliticsDTO
    population: PopulationDTO
