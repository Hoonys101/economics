# WO-137: Dynamic Intelligence & Performance (Operation Clean Sweep)

## 1. 🎯 Objective
Scale the simulation to 2,000+ agents with sub-second performance and replace rigid market rules with dynamic, intelligent systems.

## 2. 🛠️ Implementation Requirements

### Task 1: Performance Profiling & Vectorization
- **Profiling**: Create `scripts/profile_simulation.py` to identify hotspots in a 2,000 household + 200 firm scenario.
- **Vectorization**:
    - Identify bottleneck loops in `simulation/firms.py` (production cycles) and `simulation/core_agents.py` (consumption/utility math).
    - Implement **NumPy Vectorization** for batch updates of Agent state.
    - Priority: `Household.update_needs()` and `Firm.produce()`.

### Task 2: Generalized Technology (Probability Model)
- **Refactor `TechnologyManager`**:
    - Move away from "Tick-Triggered" technical triggers.
    - Implement a "Tech Diffusion" model where `TechNode` unlocking depends on:
        1. Cumulative **Corporate Capex** (Investment).
        2. **Government R&D Subsidies**.
        3. Probability factor $P(\text{unlock}) = f(\text{Investment}, \text{Subsidies}, \text{Time})$.
- **Firm Logic**: Add `invest_in_technology` method to Firms.

### Task 3: Dynamic Circuit Breaker
- **Market Logic**:
    - In `simulation/markets/core_markets.py` (or relevant market implementation), replace the constant ±15% price limit.
    - Implement a **Volatility-Adjusted Circuit Breaker**:
        - Limit = $\text{BaseLimit} \times \text{VolatilityScale}$.
        - High volatility expands the limit or triggers temporary halts.

## 3. ✅ Acceptance Criteria
1.  **Latency**: 2,000 agent tick speed < 200ms on standard hardware.
2.  **Emergence**: Technologies are unlocked via agent behavior (investment), not hardcoded clock events.
3.  **Stability**: Market volatility is managed without artificial price floors that cause inventory gluts.

## 4. 🔗 Reference
- `simulation/systems/technology_manager.py`
- `simulation/firms.py`
- `simulation/core_agents.py`
- `simulation/markets/`
