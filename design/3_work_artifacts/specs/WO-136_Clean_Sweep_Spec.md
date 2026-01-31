# Work Order: - "Operation Clean Sweep"
## (Generalization & Optimization)

> **Status**: DRAFT
> **Owner**: Antigravity
> **Priority**: CRITICAL

---

## 1. Executive Summary
The goal of this mission is to transition the simulation from a "scripted script" to a "generalized system." We are removing the scaffolding (hardcoded tech unlocks at specific ticks) and replacing it with an emergent system driven by agent decisions (R&D investment, Government subsidies). Additionally, we will optimize the engine for 2,000+ agents using NumPy vectorization and implement adaptive market safety mechanisms.

---

## 2. Technical Requirements

### 2.1 Generalize Technology (Probabilistic R&D)
- **Problem**: Tech currently unlocks at `unlock_tick` regardless of the economic state.
- **Solution**:
 - Update `TechNode` to include `research_threshold` (Total accumulated R&D investment in the sector).
 - `Firm` agents (via `CorporateManager`) can now allocate a portion of profits/assets to `rd_expenditure`.
 - **Unlock Logic**: `P(Unlock) = f(Total_Sector_RD, Cumulative_Government_Subsidies)`.
 - **Diffusion Logic**: Remains probabilistic but influenced by `firm_rd_intensity`.

### 2.2 Optimize Performance (NumPy Vectorization)
- **Target**: `TechnologyManager._process_diffusion` and `_get_effective_diffusion_rate`.
- **Method**: 
 - Convert adoption flags to a NumPy boolean array.
 - Use NumPy broadcasting to calculate diffusion for all firms in a sector in a single operation.
 - Target tick latency: < 200ms for 2,000 agents.

### 2.3 Dynamic Circuit Breakers
- **Problem**: Fixed price limits (±15%) are too rigid during transitions like the Industrial Revolution.
- **Solution**:
 - Implement `VolatilityTracker` in `OrderBookMarket`.
 - `Dynamic_Limit = Base_Limit (15%) * min(2.0, max(0.5, current_volatility / historical_avg_volatility))`.
 - Prevents "Inventory Traps" during deflationary growth (Phase 23 scenario).

---

## 3. Implementation Roadmap

### Phase A: Architecture & DTOs
1. **Modify `FirmTechInfoDTO`**: Add `rd_expenditure` (float) and `cumulative_rd` (float).
2. **Modify `ScenarioStrategy`**: Add `rd_success_base_rate` and `rd_cost_multiplier`.

### Phase B: Technology Logic (Systems)
1. **Refactor `TechnologyManager`**:
 - Remove `unlock_tick` dependency.
 - Implement `_check_probabilistic_unlocks(firms, subsidies)`.
 - Vectorize `_process_diffusion` using NumPy.

### Phase C: Market Resilience
1. **Update `OrderBookMarket`**:
 - Add `price_history` buffer for volatility calculation.
 - Implement `get_dynamic_price_bounds(item_id)`.
 - Integrity check: Ensure no transaction occurs outside dynamic bounds.

---

## 4. Success Criteria
- [ ] No hardcoded `unlock_tick` in `technology_manager.py`.
- [ ] `TechnologyManager.update` execution time reduced by > 50% for 2,000 agents.
- [ ] `Market` price moves are limited by volatility-scaled bounds.
- [ ] Industrial Revolution scenario (Phase 23) successfully triggers via R&D accumulation instead of the Tick 50 script.
