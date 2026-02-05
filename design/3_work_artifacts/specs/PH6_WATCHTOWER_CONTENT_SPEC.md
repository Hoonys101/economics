## 1. Vision & Architecture: The Container-Conveyor
"The Watchtower" is a **dynamically reconfigurable command center**. It uses a "Slot & Component" pattern to adapt its interface to the specific economic paradox being verified.

### 🏗️ Design Philosophy: Slot-Based Scaffolding
- **The Scaffolding (HTML)**: High-level page structure defined with semantic HTML tags (e.g., `main`, `section`, `article`). These serve as the permanent "Slots."
- **The Component API (JS)**: Standardized data interfaces (e.g., `ChartDataV1`, `MetricCardV1`). Any component implementing the contract can be hot-swapped into a Slot.
- **The Style (CSS)**: Each component and container has its own fully-defined, scoped CSS to ensure visual integrity during swaps.
- **Dynamic Configuration**: The system reads the active "Scenario" and maps specific components to the slots (e.g., Scenario D swaps the "Macro Plot" for a "Malthusian Population Plot").

## 2. Core Economic Scenarios (Diagnostic Capabilities)
The Watchtower must be able to visually verify the following complex phenomena.

### Scenario A: Monetary Expansion & Inflation Drift
- **Phenomenon**: Rapid M2 growth leads to CPI spikes with a time lag.
- **Verification Hook**:
  - `Overview`: CPI Sparkline turns Red.
  - `Finance`: M2 supply curve steepens, followed by a delayed rise in the Base Rate.
  - `System`: Log confirms "Central Bank: Expansionary Policy Active".

### Scenario B: The Liquidity Trap (Interbank Divergence)
- **Phenomenon**: Central Bank lowers rates, but commercial banks stop lending due to risk/liquidity fears.
- **Verification Hook**:
  - `Finance`: Interest Rate Corridor Chart shows **Base Rate falling** while **Interbank Call Rate spikes or NaN**.
  - `Macro`: GDP growth stagnates despite low nominal rates.

### Scenario C: Social Tipping Point (Inequality Trap)
- **Phenomenon**: Economic growth benefits only the top quintile, leading to social unrest and election risk.
- **Diagnostics**: Gini Coefficient + Approval (Lower Quintile) vs Approval (Top Quintile).

### Scenario D: Malthusian Trap (Resource Exhaustion)
- **Phenomenon**: Population growth outpaces resource production (Food), leading to per-capita subsistence decline.
- **Diagnostics**: Population Curve vs Food Production (Dual Axis) + Average Hunger/Needs Fulfillment.

### Scenario E: The Great Leveler (Black Death/Pandemic)
- **Phenomenon**: Sudden mass extinction of specific demographics (e.g., Low-Income workers) causing labor shortage and wage spikes.
- **Diagnostics**: Mortality Heatmap by Income + Sectoral Wage Fluctuations + GDP contraction.

---

## 2. Definitive Indicator Matrix (The Field List)

### 📍 HUD (The Situation Room)
- **Real-Time FPS**: Engine performance.
- **M2 Leak (Delta)**: Must be `0.0000`. Trigger full-screen strobe if `> 0.0001`.
- **GDP Growth (SMA-20)**: Moving average to smooth noise.
- **Active Population**: Total agent count.

### 📍 Finance Page (The Bank) [UPDATED]
- **Interest Rate Corridor**: [Base Rate, Interbank Call Rate, Avg Savings Rate, Avg Loan Rate].
- **Liquidity Ratios**: M0 (Base) / M2 (Broad).
- **Money Velocity**: (Nominal GDP / M2).
- **Multi-Currency**: Real-time exchange rates (converted to DEFAULT_CURRENCY).

### 📍 Politics Page (The Capitol) [NEW]
- **Political Pulse**: Approval Rating (By Quintile), Social Cohesion.
- **Fiscal Flow**: Tax Revenue History, Welfare Spending, National Debt/GDP.
- **Governance Status**: Ruling Party, Active Policy Lockouts.

### 📍 Population Page (The Field)
- **Household Heatmap**: Income vs Assets grid.
- **Filtering Dimensions**:
  - `Class`: 5-bin income distribution.
  - `Age`: Generation (0, 1, 2+).
  - `Employment`: Student, Worker, Entrepreneur, Unemployed.
- **Vitality**: Birth rate vs Death rate sparklines.

---

## 3. Structural Deliverables (Step 2 Preview)

| Page | Primary Component | Interactive Feature |
|:---|:---|:---|
| `Overview` | KPI Cards + Live Ticker | "System Integrity" Emergency strobe. |
| `Finance` | Multi-line Area Chart | Toggle individual rate visibility. |
| `Politics` | Sankey Diagram (Fiscal Flow) | View "Advice History" from AI advisors. |
| `System` | Searchable Log Terminal | Filter logs by [Agent, Sector, Error Level]. |

---

## 4. Confirmation Gate
**Awaiting User Review on Section 1 & 2.**  
Next Step (Step 2) will generate the precise JSON types for these fields.
