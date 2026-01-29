# Work Order: WO-140 - Repository Decomposition

## 🎯 Objective
Decompose the monolithic `SimulationRepository` (745+ LOC) in `simulation/db/repository.py` into specialized, entity-focused repositories. This will improve maintainability, reduce cognitive load, and align with the Separation of Concerns (SoC) principle.

---

## 🛠️ Tasks

### 1. Create specialized repositories
Create the following files in `simulation/db/`:
- `agent_repository.py`: CRUD and analytics for agent states.
- `market_repository.py`: CRUD for transactions and market history.
- `analytics_repository.py`: CRUD for economic indicators and AI decisions.
- `run_repository.py`: CRUD for simulation run metadata.

### 2. Move Logic
- **`AgentRepository`**: Move `save_agent_state`, `save_agent_states_batch`, `get_agent_states`, `get_generation_stats`, `get_attrition_counts`.
- **`MarketRepository`**: Move `save_transaction`, `save_transactions_batch`, `save_market_history`, `save_market_history_batch`, `get_transactions`, `get_market_history`.
- **`AnalyticsRepository`**: Move `save_economic_indicator`, `save_economic_indicators_batch`, `get_economic_indicators`, `get_latest_economic_indicator`, `save_ai_decision`.
- **`RunRepository`**: Move `save_simulation_run`, `update_simulation_run_end_time`.

### 3. Implement Base Class or Mixins
- Consider a base class or shared logic for database connection management (`self.conn`, `self.cursor`).
- Ensure all new repositories use `simulation.db.database.get_db_connection`.

### 4. Update Orchestrator (`SimulationRepository`)
- Refactor `SimulationRepository` to act as a composition of these new repositories or a simplified facade.
- Update `clear_all_data` to delegate to sub-repositories if necessary.

### 5. Dependency Update
- Update all references to `SimulationRepository` in the codebase to use either the specialized repositories or the new refactored facade.

---

## 🏗️ Technical Constraints
- No changes to the database schema.
- Maintain existing API signatures to minimize breakage in callers.
- Ensure `SimulationRepository.close()` properly handles connection closing for all components.

---

## 🏁 Success Sign-off
- [ ] `SimulationRepository` is decomposed into 4 specialized files.
- [ ] No regression in data persistence or retrieval (verify via existing tests).
- [ ] Code cleanliness: All god-file symptoms (excessive LOC, mixed responsibilities) resolved.
