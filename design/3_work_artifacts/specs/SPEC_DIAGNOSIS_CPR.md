# Operation CPR: Economic Resuscitation Plan

**Date**: 2026-01-30
**Status**: DRAFT
**Objective**: Diagnose and resolve the "Brain Death" state (GDP 0.0, CPI Stagnant) of the simulation.

---

## 1. Situation Analysis
The `PhenomenaAnalysis` report (2026-01-30) indicates a complete economic standstill:
- **GDP**: 0.0 (No transactions)
- **CPI**: Fixed at 302.34 (No price discovery)
- **ZLB Hit**: Central Bank at 0% interest with no effect.
- **Resilience Score**: 100.0 (False positive due to zero volatility).

## 2. Root Cause Hypotheses

### A. The "Black Hole" Hypothesis (Confirmed)
- **Mechanism**: `HousingSystem` directly subtracts assets (`_sub_assets`) from agents without routing them to a receiver via `SettlementSystem` or creates money (`_add_assets`) from thin air during loan fallbacks.
- **Evidence**: 900k M2 Drift observed in previous audits. Code review confirms bypass of `SettlementSystem`.
- **Impact**: Households are drained of liquidity, preventing them from bidding in the Goods Market.

### B. The "Straitjacket" Hypothesis (Suspected)
- **Mechanism**: `OrderBookMarket` implements a dynamic Circuit Breaker. If the initial volatility is 0 (no trades), the allowed price range might be too narrow or effectively closed if logic fails.
- **Evidence**: `OrderBookMarket.py` has logic to reject orders outside bounds. If bounds initialization fails or locks, no orders are accepted.

### C. The "Bid-Ask Gap" Hypothesis (Suspected)
- **Mechanism**: Firms' Cost of Goods Sold (COGS) forces a high Ask Price, while Households' lack of liquidity forces a low Bid Price. If `Bid < Ask` universally, no transactions occur.
- **Impact**: Permanent market freeze.

---

## 3. Surgical Plan (Execution Steps)

We will proceed with a **"Fix -> Relax -> Stimulate"** cadence.

### Step 1: Stop the Bleeding (Refactor Housing)
**Goal**: Ensure Money Conservation (Zero-Sum).
- **Action**: Refactor `simulation/systems/housing_system.py`.
    - Replace direct `agent.assets` modification with `simulation.settlement_system.transfer()`.
    - Implement `transfer(buyer, seller, amount, "property_purchase")`.
    - Implement `transfer(tenant, owner, amount, "rent")`.
    - Ensure Mortgage Loan creation uses `bank.grant_loan` correctly without "air money" fallback.

### Step 2: Remove the Straitjacket (Disable Breakers)
**Goal**: Ensure Order Acceptance.
- **Action**: Create a diagnosis config `config/scenarios/diagnosis_free_market.yaml`.
    - Set `MARKET_CIRCUIT_BREAKER_BASE_LIMIT` to `100.0` (Effectively disabled).
    - Or add a flag `ENABLE_CIRCUIT_BREAKER: false` to `OrderBookMarket`.

### Step 3: Jumpstart the Heart (Stimulus)
**Goal**: Force a Trade.
- **Action**: Update `diagnosis_free_market.yaml`.
    - **Super Households**: `initial_cash: 50000` (High purchasing power).
    - **Super Firms**: `initial_inventory: 1000` (High supply).
    - **Reasoning**: If GDP remains 0 even with infinite money and supply, the **Matching Engine** itself is broken.

---

## 4. Verification Protocol
After each step, run:
```powershell
python scripts/run_phenomena_analysis.py --scenario config/scenarios/diagnosis_free_market.yaml
```
**Success Metric**: `GDP > 0.0`.

---

## 5. Work Orders
- **WO-156**: Fix Housing System Leak (Step 1).
- **WO-157**: Diagnostic Config & Market Unlock (Step 2 & 3).
