# Work Order: WO-136 - Operation Clean Sweep

## 🎯 Objective
Transition the simulation from "Scripted Events" to a "Generalized System." Move away from hardcoded tech timestamps and fixed market limits, replacing them with agent-driven emergence and adaptive safety bounds. Optimize for 2,000+ agents.

---

## 🛠️ Tasks

### 1. Generalize Technology (System/Tech)
- **Path**: `simulation/systems/technology_manager.py`
- **Action**:
    - Remove `unlock_tick` from `TechNode`.
    - Implement `_check_probabilistic_unlocks`. A technology should have a chance to unlock each tick based on the **Total accumulated R&D investment** in its sector.
    - Base formula for unlock chance: `P = min(0.1, (Sector_Accumulated_RD / Tech_Cost_Threshold)^2)`.
    - Update `FirmTechInfoDTO` in `simulation/systems/tech/api.py` to include `current_rd_investment`.

### 2. Optimize for 2,000+ Agents (Vectorization)
- **Action**:
    - Refactor `TechnologyManager._process_diffusion` to use **NumPy**.
    - Instead of looping through all firms and checking `random.random() < rate`, use `np.random.rand(num_firms) < rates` and update flags via boolean indexing.
    - Benchmark the tick latency using `scripts/profile_simulation.py` (if exists) or simple time delta logging.

### 3. Dynamic Circuit Breakers (Markets)
- **Path**: `simulation/markets/order_book_market.py`
- **Action**:
    - Add a price history buffer (last 20 prices) per item.
    - Calculate **Standard Deviation (Volatility)** of prices.
    - Implement `get_dynamic_price_bounds`.
    - Replace the hardcoded ±15% logic (if it exists in `place_order` or `match_orders` - check `Simulation` logic too) with `Bounds = Prev_Avg * (1 ± (Base_Limit * Volatility_Adj))`.

---

## 🏗️ Technical Constraints
- No direct agent access. Use DTOs.
- Maintain Purity Gate standards (verify via `scripts/verify_purity.py`).
- Do not break the "Industrial Revolution" outcome (it should still occur, but via high R&D investment).

---

## 🏁 Success Sign-off
- [ ] Technology unlocks are stochastic and tied to firm spending.
- [ ] Tick latency < 150ms for 2,000 agents.
- [ ] Market prices show adaptive volatility bounds.
