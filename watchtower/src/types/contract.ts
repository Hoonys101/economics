export interface SystemIntegrity {
  /** Unit: Currency */
  m2_leak: number;
  /** Simulation speed */
  fps: number;
}

export interface MacroEconomy {
  /** Percentage (%) */
  gdp_growth: number;
  /** Percentage (%) */
  inflation_rate: number;
  /** Percentage (%) */
  unemployment_rate: number;
  /** 0.0 - 1.0 */
  gini_coefficient: number;
}

export interface Monetary {
  /** Central Bank Rate (%) */
  base_rate: number;
  /** Market Call Rate (%) */
  interbank_rate: number;
  /** Total Money */
  m2_supply: number;
  /** e.g., {"KRW": 1400.0} */
  exchange_rates: Record<string, number>;
}

export interface Politics {
  party: 'RED' | 'BLUE' | 'NEUTRAL';
  /** 0.0 - 1.0 */
  approval_rating: number;
  /** 0.0 - 1.0 */
  social_cohesion: number;
  /** List of significant tick events */
  current_events: string[];
}

export interface WatchtowerSnapshot {
  tick: number;
  /** ISO-8601 */
  timestamp: string;
  system_integrity: SystemIntegrity;
  macro_economy: MacroEconomy;
  monetary: Monetary;
  politics: Politics;
}
