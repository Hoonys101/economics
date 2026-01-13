# WO-056 Stage 1 Insight Report

## 1. Overview
This report documents the completion of **WO-056 Stage 1: Invisible Hand (Shadow Mode)** and the resolution of the **Currency Leakage** issue.

## 2. Currency Leakage Resolution
### 2.1 The Issue
The simulation exhibited a consistent money leak of **-40.0** per tick (and a massive initial leak of **-914.8** in previous versions).
- **Analysis:** The leak was traced to **Marketing Spend** (and R&D/Automation/CAPEX) not being captured by the `EconomicRefluxSystem`.
- **Root Cause:**
    1. `CorporateManager` methods (`_manage_r_and_d`, `_manage_automation`) were depleting assets without invoking `reflux_system.capture`.
    2. A critical initialization bug in `simulation/engine.py`: The `Firm.update_needs` method was called during `Simulation.__init__` with `reflux_system=None` (default), causing initial marketing expenses to vanish.

### 2.2 The Fix
1. **Reflux Injection:** Updated `CorporateManager` to accept and use `reflux_system` for all investment channels.
2. **Initialization Order:** Moved `self.reflux_system = EconomicRefluxSystem()` to the top of `Simulation.__init__` and ensured it is passed to `Firm.update_needs` during the initial setup loop.
3. **Verification:** `tests/verify_economic_equilibrium.py` now passes with conservation of money confirmed (accounting for valid creation/destruction events).

## 3. Shadow Mode Implementation
The "Invisible Hand" mechanisms have been implemented in **Shadow Mode** (Logging Only), ensuring no functional impact on the current economy.

### 3.1 Firms (Price Discovery)
- **Method:** `_calculate_invisible_hand_price`
- **Logic:** `Shadow_Price = Current_Price * (1 + Sensitivity * Excess_Demand_Ratio)`
- **Sensitivity:** Set to **0.1**.
- **Observation:** Logs show stable shadow prices (e.g., `10.00 -> 9.80`) with `ExcessRatio: -1.0` (indicating high inventory/low demand saturation). The 0.1 sensitivity provides smooth guidance without volatility.

### 3.2 Households (Wage Reservation)
- **Method:** `_calculate_shadow_reservation_wage`
- **Logic:**
    - Employed: +5% (Confidence)
    - Unemployed: -2% (Decay)
- **Observation:** Shadow wages track employment status correctly, creating a "Sticky Wage" pressure that prevents rapid deflation while allowing upward mobility.

### 3.3 Government (Taylor Rule 2.0)
- **Method:** `_calculate_shadow_target_rate`
- **Logic:** `Target = Real_Growth + Inflation + 0.5 * (Inflation Gap) + 0.5 * (GDP Gap)`
- **Observation:** The shadow rate provides a counter-cyclical benchmark against the fixed/simple `CentralBank` rate.

## 4. Future Risk Warning (Critical)
During stress testing (`iron_test.py`), a secondary massive leak (**-126k**) was observed during **Firm Liquidation**.
- **Cause:** When a firm liquidates, cash is distributed to **active** shareholders only. If a shareholder is **inactive** (dead/bankrupt) but not yet processed/cleared, their share of the liquidation proceeds is **destroyed** (skipped in distribution loop) rather than Escheated to Government or preserved.
- **Recommendation:** Refactor `_handle_agent_lifecycle` to track unclaimed liquidation proceeds and transfer them to the Government (Escheatment) or Reflux System to maintain conservation of money.

## 5. Conclusion
Stage 1 is complete. The simulation is leak-free under normal operation, and Shadow Mode is generating valuable telemetry for Phase 2 tuning.
