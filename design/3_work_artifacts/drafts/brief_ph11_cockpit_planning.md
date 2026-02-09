# Cockpit Planning Brief: Phase 11 (The Simulation Cockpit)

## 1. Current State of Observability
The simulation currently has a foundational data aggregation layer called **The Watchtower** and a **Dashboard Service**.

### Available Metrics (Vitals)
- **Macro**: Nominal GDP (100-tick SMA), Consumer Price Index (CPI), Unemployment Rate, Gini Coefficient.
- **Financial**: M0/M1/M2 Supply, Velocity of Money, Base Rate, Loan/Call Market Rates.
- **Integrity**: **M2 Leak detection** (Critical audit), FPS/Tick-speed.
- **Population**: Active count, Birth/Death rates (Attrition tracking).

### Deep-Dive Capabilities
- **System 2 Insights**: Ability to see an agent's internal world model (NPV of wealth, projected bankruptcy tick).
- **Social Cohesion**: Tracking ruling party approval and societal stress.

## 2. The Implementation Gap (What to Build)
Currently, data exists in DTOs, but the **Frontend UI** is disconnected or exists as a skeletal Next.js/Streamlit app.

### Vision: What to See
- **Wealth Distribution Heatmap**: Real-time view of assets across quintiles.
- **Crisis Alarm**: Visual alerts when M2 velocity drops or Gini exceeds thresholds.
- **Policy Diffusion**: Visualizing how Central Bank rate changes propagate to individual agent consumption.

### Vision: What to Judge (The "God-Mode" Levers)
- **Rate Control**: Setting the `BASE_INTEREST_RATE` in real-time.
- **Tax Tuning**: Adjusting `AUTOMATION_TAX` or `WELFARE_RATIO` on the fly.
- **Shock Injection**: Manually triggering a "Bank Run" or "Supply Chain Disaster" to test resilience.

## 3. Planning Decision for Architect Prime
To proceed with Phase 11, we need to decide on the primary UI focus:
1.  **Macro-Audit Focus**: High-level charts and M2 integrity verification (Safety first).
2.  **Sociological Focus**: Tracking individual "System 2" decisions and belief propagation (Understanding the "Why").
3.  **Active Governance Mode**: Real-time policy adjustment sliders (Interaction focus).

---
**Status**: The `DashboardService` is ready to stream these DTOs via WebSockets. We await a priority directive for the UI focus.
