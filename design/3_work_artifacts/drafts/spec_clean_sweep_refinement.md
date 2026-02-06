# Work Order: Operation Clean Sweep Refinement (Track 2)

## 1. Objective
Bridge the gap between individual firm behavior and emergent global systems, and optimize performance for 2,000+ agents.

## 2. Technical Requirements

### 2.1 R&D Integration Bridge
- **Problem**: `Firm` agents invest in R&D via `ProductionDepartment`, but this data is not passed to `TechnologyManager` for global sector unlocks.
- **Tasks**:
  - Update the orchestrator (e.g., `Simulation.run_tick`) to aggregate `current_rd_investment` from all firms into `FirmTechInfoDTO`.
  - Pass this aggregated data to `TechnologyManager.update`.
  - Ensure `check_probabilistic_unlocks` uses real accumulated capital from firms.

### 2.2 Performance & Benchmarking
- **Tasks**:
  - Verify `TechnologyManager._process_diffusion` vectorization.
  - Create a benchmark script `scripts/bench_tech.py` to measure 2,000 agents / 1,000 ticks.
  - Optimization Goal: < 10ms per tick for tech diffusion.

### 2.3 Market Integrity (Circuit Breakers)
- **Tasks**:
  - Validate `OrderBookMarket.get_dynamic_price_bounds` against heavy volatility scenarios.
  - Ensure `MARKET_CIRCUIT_BREAKER_BASE_LIMIT` (default 0.15) is properly honored and logged.

## success Criteria
- Tech nodes unlock based on sector-wide firm R&D spending.
- Simulation maintains 10+ FPS with 2,000 active agents.
- No monetary leakage during tech unlocks/diffusion.
