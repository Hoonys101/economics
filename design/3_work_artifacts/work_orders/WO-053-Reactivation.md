# Work Order: Phase 23 Reactivation (The Great Expansion)

## 1. Overview
**Mission**: Reactivation
**Objective**: Escape the Malthusian Trap by successfully introducing Chemical Fertilizer (Haber-Bosch) and triggering a population boom via food surplus.
**Target Metrics**:
1. **Supply/Demand Ratio >= 2.5** (Verification of Glut)
2. **Price Crash > 50%** within 20 ticks of introduction.
3. **Population Boom** leading to max agents limit (2000).

---

## 2. Configuration Requirements
Target File: `config/scenarios/phase23_industrial_rev.json`

Ensure the configuration is set to the following values to force "Radical Change":

```json
{
 "SCENARIO_ID": "PHASE_23_INDUSTRIAL_REV",
 "DESCRIPTION": "The Great Expansion: Fertilizer & Population Boom",
 "PARAMETERS": {
 "TFP_MULTIPLIER": 3.0,
 "FOOD_SECTOR_CONFIG": {
 "base_productivity": 10,
 "technology_bonus": 2.0
 },
 "MARKET_CONFIG": {
 "PRICE_VOLATILITY_LIMIT": 0.5
 },
 "LIMITS": {
 "MAX_AGENTS": 2000,
 "MAX_TICK_LATENCY_SEC": 1.0
 }
 }
}
```

*Note: You may need to adapt the JSON structure to match the actual schema of `config.py` or `ScenarioLoader`. The key is to achieve a 3.0x TFP boost in the Food sector.*

---

## 3. Implementation Steps

### Step 1: Scenario Configuration
- Load `phase23_industrial_rev.json`.
- Ensure `TechnologyManager` applies the `TFP_MULTIPLIER` of 3.0 to all `FoodSector` firms starting from Tick 50 (or appropriate phase trigger).

### Step 2: Market Logic Tuning
- In `MarketMatching` logic, ensure there are no artificial floors preventing a 50% price drop.
- If a "Circuit Breaker" exists (e.g., max 10% change per tick), **DISABLE** it or widen it to 50% for this scenario.

### Step 3: Verification Script (`scripts/verify_phase23.py`)
- The script must run the simulation for at least 100 ticks (or until limits are hit).
- It must log and analyze:
 - **Global Food Supply vs Demand** (Ask Qty / Bid Qty).
 - **Average Food Price**.
 - **Total Population**.
- **Success Criteria**:
 - `Max(Supply/Demand) >= 2.5`
 - `Price(Tick + 20) <= Price(Tick) * 0.5` (50% crash)
 - `Population(End) > Population(Start) + 200` (Significant growth)

---

## 4. Execution & Reporting
- Run the verification.
- Output a report summarizing:
 - Tick of Fertilizer Introduction.
 - Tick of Price Crash.
 - Peak Supply/Demand Ratio.
 - Final Population count.
 - Pass/Fail verdict based on metrics.

**Constraint**: If `Tick Latency > 1.0s`, abort and report "Performance Fail".
**Constraint**: If `Population > 2000`, stop and report "Success (Boom Limit Reached)".
