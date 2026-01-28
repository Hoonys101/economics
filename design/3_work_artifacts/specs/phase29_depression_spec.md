# Zero-Question Spec: Phase 29 - "The Great Depression" (Stress Test)

**ID:** Phase-29
**Author:** Antigravity (Team Leader)
**Reviewer:** Architect Prime
**Subject:** Liquidity Crisis Simulation and Solvency Logic Verification

---

## 1. Executive Summary

Now that **TD-008 (Altman Z-Score)** and **Phase 28 (Behavioral Psych)** are integrated, we must verify the system's resilience under extreme stress. Phase 29 simulates a "Great Depression" scenario to test if the Z-Score logic accurately identifies distressed firms and if the Bailout Protocol prevents systemic collapse without enabling "zombie firms."

## 2. Experimental Design: "Black Thursday" Scenario

### 2.1. Scenario Triggers
An artificial Credit Crunch will be initiated at a specific tick to observe the transition from growth to depression.

*   **Monetary Shock**: Sharp increase in `base_rate` (Central Bank). Target: 0.08 (8%).
*   **Fiscal Shock**: Increase in `corporate_tax_rate` (Government). Target: 0.30 (30%).

### 2.2. Expected Chain Reaction
1.  Increased interest burden for firms.
2.  Drop in net profits, leading to lower Retained Earnings.
3.  **Altman Z-Score Migration**: Movement from Safe Zone (> 2.99) to Distress Zone (< 1.81).
4.  Triggering of `FinanceSystem.evaluate_solvency` and subsequent Bailout or Liquidation.

## 3. Implementation Requirements

### 3.1. Work Item 1: Scenario Configuration
Create a new scenario configuration file: `config/scenarios/phase29_depression.json`.
This file should define the overrides for the simulation parameters as specified by Architect Prime.

### 3.2. Work Item 2: Crisis Monitoring Module
Implement a new analysis tool: `modules/analysis/crisis_monitor.py`.

*   **Functionality**:
    *   Collector: Iterates through all active firms every tick.
    *   Classifier: Categorizes firms based on Altman Z-Score:
        *   **Safe**: Z > 2.99
        *   **Gray**: 1.81 <= Z <= 2.99
        *   **Distress**: Z < 1.81
    *   Logger/Reporter: Generates a time-series log (CSV or JSON) of these counts and the overall survival rate.

### 3.3. Work Item 3: Integration with Engine
Update `simulation/engine.py` (or the appropriate system) to call the `CrisisMonitor` during the simulation loop and log the distribution.

## 4. Verification & Reporting

### 4.1. Success Criteria
*   The simulation successfully triggers the shocks at the defined tick.
*   The `CrisisMonitor` correctly logs the migration of Z-Scores.
*   The system distinguishes between "Salvageable" firms (Safe/Gray) and "Distressed" firms according to the new logic.

### 4.2. Reporting (Technical Debt)
Per the SCR protocol, the implementer (Jules) must report:
1.  Any implementation bottlenecks in the new monitoring logic.
2.  Observations on Z-Score sensitivity (Does it drop too fast? Too slow?).
3.  Any "Dirty Hacks" required to override the Central Bank/Government behavior.
