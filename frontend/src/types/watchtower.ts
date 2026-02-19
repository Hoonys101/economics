export interface IntegrityDTO {
    m2_leak: number;
    fps: number;
}

export interface MacroDTO {
    gdp: number;
    cpi: number;
    unemploy: number;
    gini: number;
}

export interface FinanceRatesDTO {
    base: number;
    call: number;
    loan: number;
    savings: number;
}

export interface FinanceSupplyDTO {
    m0: number;
    m1: number;
    m2: number;
    velocity: number;
}

export interface FinanceDTO {
    rates: FinanceRatesDTO;
    supply: FinanceSupplyDTO;
}

export interface PoliticsApprovalDTO {
    total: number;
    low: number;
    mid: number;
    high: number;
}

export interface PoliticsStatusDTO {
    ruling_party: string;
    cohesion: number;
}

export interface PoliticsFiscalDTO {
    revenue: number;
    welfare: number;
    debt: number;
}

export interface PoliticsDTO {
    approval: PoliticsApprovalDTO;
    status: PoliticsStatusDTO;
    fiscal: PoliticsFiscalDTO;
}

export interface PopulationDistributionDTO {
    q1: number;
    q2: number;
    q3: number;
    q4: number;
    q5: number;
}

export interface PopulationMetricsDTO {
    birth: number;
    death: number;
}

export interface PopulationDTO {
    distribution: PopulationDistributionDTO;
    active_count: number;
    metrics: PopulationMetricsDTO;
}

export interface WatchtowerSnapshotDTO {
    tick: number;
    timestamp: number;
    status: string;
    integrity: IntegrityDTO;
    macro: MacroDTO;
    finance: FinanceDTO;
    politics: PoliticsDTO;
    population: PopulationDTO;
}
