export interface GenerationStat {
  generation: number;
  count: number;
  avg_assets: number;
}

export interface SocietyTabData {
  generations: GenerationStat[];
  mitosis_cost: number;
  unemployment_pie: {
      struggling: number;
      voluntary: number;
  };
  // Phase 5
  time_allocation: Record<string, number>;
  avg_leisure_hours: number;
}

export interface GovernmentTabData {
  tax_revenue: Record<string, number>;
  fiscal_balance: {
      revenue: number;
      expense: number;
  };
  // Phase 5
  tax_revenue_history: Record<string, any>[]; // Array of history objects
  welfare_spending: number;
  current_avg_tax_rate: number;
  welfare_history: Record<string, number>[];
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
  // Phase 5
  avg_tax_rate: number;
  avg_leisure_hours: number;
  parenting_rate: number;
}

export interface DashboardSnapshot {
  tick: number;
  global_indicators: DashboardGlobalIndicators;
  tabs: {
      society: SocietyTabData;
      government: GovernmentTabData;
      market: MarketTabData;
      finance: FinanceTabData;
  };
}
