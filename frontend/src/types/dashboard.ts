export interface DashboardSnapshot {
  tick: number;
  global_indicators: {
    death_rate: number;
    bankruptcy_rate: number;
    employment_rate: number;
    gdp: number;
    avg_wage: number;
    gini: number;
  };
  society_tab: {
    generation_stats: Array<{
      generation: number;
      count: number;
      avg_assets: number;
    }>;
    unemployment_pie: Record<string, number>;
  };
  government_tab: {
    tax_revenue: Record<string, number>;
    expenditure_history: number[];
  };
  market_tab: {
    cpi: number[];
    trade_volume: number[];
    maslow_fulfillment: number[];
  };
  finance_tab: {
    market_cap: number;
    volume: number;
    turnover: number;
  };
}
