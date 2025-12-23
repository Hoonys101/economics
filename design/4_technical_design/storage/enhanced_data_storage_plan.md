# Enhanced Data Storage and Debugging Plan

## 1. Problem Recognition
Currently, debugging the economic simulation relies heavily on log files (`app.log`). While these logs provide valuable real-time information, they are often truncated, difficult to parse for specific data points across multiple ticks, and do not allow for easy state inspection or re-simulation from a particular point in time. The absence of transaction records in the database, despite log indications of successful matches, highlights the limitations of the current approach.

## 2. Proposed Solution: Comprehensive Database Storage per Tick

To address the debugging challenges and enable advanced simulation features, we propose enhancing the data storage strategy to save comprehensive simulation state and event data directly into the SQLite database (`simulation_data.db`) at each tick.

### 2.1. Goals
*   Enable easy inspection of simulation state at any given tick.
*   Facilitate debugging by providing structured, queryable data.
*   Lay the groundwork for features like:
    *   Reverting to a previous simulation tick.
    *   Re-running simulations from a specific saved state.
    *   Detailed post-simulation analysis without extensive log parsing.

### 2.2. Data Points to Store (per tick)

#### a. Agent States (Enhanced `agent_states` table)
*   **Existing:** `time`, `agent_id`, `agent_type`, `assets`, `is_active`, `is_employed`, `employer_id`, `needs_survival`, `needs_labor`, `inventory_food`, `current_production`, `num_employees`.
*   **Proposed Enhancements:**
    *   **Household-specific:** All current needs (`survival`, `social`, `improvement`, `asset`, `imitation`, `liquidity`, `child_rearing`), current inventory of all goods, chosen `value_orientation`, `personality`.
    *   **Firm-specific:** All current inventory of all goods, `production_targets` for all goods, `productivity_factor`, `revenue_this_turn`, `expenses_this_tick`, `profit_history` (perhaps as a serialized JSON or a separate table).
    *   **AI Decision Details:**
        *   `chosen_intention` (for both HouseholdAI and FirmAI)
        *   `chosen_tactic` (for both HouseholdAI and FirmAI)
        *   `predicted_reward` (for the chosen action)
        *   `strategic_state` (serialized JSON of the state used for strategic decision)
        *   `tactical_state` (serialized JSON of the state used for tactical decision)

#### b. Transaction Details (Enhanced `transactions` table)
*   **Existing:** `id`, `time`, `buyer_id`, `seller_id`, `item_id`, `quantity`, `price`, `market_id`, `transaction_type`.
*   **Proposed Enhancements:** No immediate changes needed, but ensure all matched transactions are correctly saved. The current issue of empty table needs to be resolved first.

#### c. Market History (Enhanced `market_history` table)
*   **Existing:** `id`, `time`, `market_id`, `item_id`, `avg_price`, `trade_volume`, `best_ask`, `best_bid`.
*   **Proposed Enhancements:** Ensure `item_id` is consistently captured for all relevant markets (e.g., `goods_market` can have multiple `item_id`s).

#### d. Simulation Events (New `simulation_events` table)
*   **Purpose:** Store significant events that occur during a tick, such as agent creation/destruction, employment changes, loan applications/approvals, skill acquisitions, etc.
*   **Schema:**
    *   `id INTEGER PRIMARY KEY AUTOINCREMENT`
    *   `time INTEGER NOT NULL`
    *   `event_type TEXT NOT NULL` (e.g., 'AGENT_CREATED', 'AGENT_DESTROYED', 'EMPLOYED', 'UNEMPLOYED', 'LOAN_GRANTED', 'SKILL_ACQUIRED')
    *   `agent_id INTEGER` (relevant agent)
    *   `related_agent_id INTEGER` (e.g., employer_id for employment events)
    *   `item_id TEXT` (e.g., skill_id for skill acquisition)
    *   `details TEXT` (serialized JSON for additional context, e.g., reason for agent destruction, loan amount)

## 3. Implementation Plan

1.  **Modify `simulation/db/schema.py`:**
    *   Update `agent_states` table schema to include new columns for detailed needs, inventory, and AI decision details.
    *   Create the new `simulation_events` table.
2.  **Modify `simulation/models.py`:**
    *   Update `Household` and `Firm` models to store the additional state and AI decision data.
3.  **Modify `simulation/db/repository.py`:**
    *   Update `save_agent_state` to handle the new columns.
    *   Implement `save_simulation_event` for the new table.
    *   **Crucially, debug and fix the current issue where `save_transaction` is not persisting data.** This will involve adding more granular logging within `save_transaction` and verifying the `conn.commit()` behavior.
4.  **Modify `simulation/engine.py`:**
    *   Adjust `run_tick` to capture and pass the enhanced agent state and AI decision data to `SimulationRepository` at the end of each tick.
    *   Integrate calls to `save_simulation_event` for relevant events.
5.  **Modify Agent Decision Engines (`HouseholdDecisionEngine`, `FirmDecisionEngine`):**
    *   Ensure that these engines capture and make available the `chosen_intention`, `chosen_tactic`, `predicted_reward`, `strategic_state`, and `tactical_state` for storage.
6.  **Update Logging:** Adjust existing logging to complement the new database storage, focusing on high-level summaries in logs and detailed data in the DB.

## 4. Verification Method
After implementing these changes, we will:
1.  Run the simulation for a few ticks.
2.  Query the `simulation_data.db` directly to verify that all new data points are correctly stored in the respective tables.
3.  Confirm that `transactions` are now correctly recorded.
4.  Analyze the stored data to ensure it accurately reflects the simulation's progression and agent decisions.

This enhanced data storage will provide a robust foundation for future development, debugging, and analysis of the economic simulation.

---
**User Confirmation Required:** Do you agree with this enhanced data storage plan?
