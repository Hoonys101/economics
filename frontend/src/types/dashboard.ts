export interface GenerationStat {
  generation: number;
  count: number;
  avg_assets: number;
}

export interface SocietyTabData {
  generations: GenerationStat[];
  mitosis_cost: number; // Added from component usage
  unemployment_pie: {
      struggling: number;
      voluntary: number;
  };
}

export interface GovernmentTabData {
  tax_revenue: Record<string, number>;
  fiscal_balance: {
      revenue: number;
      expense: number;
  };
}

export interface MarketTabData {
  commodity_volumes: Record<string, number>;
  cpi: number[];
  maslow_fulfillment: number[];
}

export interface FinanceTabData {
  market_cap: number;
  volume: number;
  turnover: number;
  dividend_yield: number;
}

export interface DashboardGlobalIndicators {
  death_rate: number;
  bankruptcy_rate: number;
  employment_rate: number;
  gdp: number;
  avg_wage: number;
  gini: number;
}

export interface DashboardSnapshot {
  tick: number;
  global_indicators: DashboardGlobalIndicators;
  // Note: The backend returns 'tabs' which contains these.
  // We need to match the actual API response structure.
  // Based on snapshot_viewmodel.py: return DashboardSnapshotDTO(tabs={...})
  tabs: {
      society: SocietyTabData;
      government: GovernmentTabData;
      market: MarketTabData;
      finance: FinanceTabData;
  };
}
