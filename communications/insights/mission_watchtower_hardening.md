# Technical Insight Report: Watchtower Hardening (Track A)

## 1. Problem Phenomenon
- **Symptoms**:
    - The Watchtower Dashboard displayed instantaneous (noisy) values for key economic indicators like GDP, CPI, and M2 Leak, making trend analysis difficult.
    - Demographic metrics were incomplete, showing Death Rate but missing Birth Rate, preventing a complete view of population dynamics.
- **Stack Trace/Logs**: N/A (Feature Gap, not a crash).

## 2. Root Cause Analysis
- **Missing Data Processing**: The `EconomicIndicatorTracker` only stored raw history in lists but did not compute moving averages for real-time consumption.
- **Missing Repository Method**: The `AgentRepository` lacked a query method to track "New Agents" (Births) comparable to the existing `get_attrition_counts` (Deaths/Bankruptcy).
- **Service Gap**: `DashboardService` was calculating `m2_leak` locally based on instantaneous snapshots rather than using a smoothed metric from the Tracker.

## 3. Solution Implementation Details
### A. Tracker Hardening (`EconomicIndicatorTracker`)
- **Deque Implementation**: Added `collections.deque(maxlen=50)` for `gdp`, `cpi` (goods_price_index), and `m2_leak`.
- **Logic**: Updated `track()` to accept `m2_leak` (calculated in Orchestrator) and append values to history.
- **API**: Added `get_smoothed_values()` to return the simple moving average (SMA) of the history.

### B. Repository Upgrade (`AgentRepository`)
- **New Method**: Implemented `get_birth_counts(start_tick, end_tick, run_id)`.
- **Logic**: Defines "Births" as the count of agents present at `end_tick` who were **NOT** present at `start_tick`. This effectively counts new survivors in the window.
- **Query**:
  ```sql
  SELECT COUNT(DISTINCT agent_id)
  FROM agent_states
  WHERE time = ? AND agent_type = 'household'
  AND agent_id NOT IN (
      SELECT agent_id FROM agent_states
      WHERE time = ? AND agent_type = 'household'
  )
  ```

### C. Orchestration Integration
- **TickOrchestrator**: Updated `_finalize_tick` to pass the calculated M2 delta to the tracker.
- **DashboardService**: Updated `get_snapshot` to prefer smoothed values from the tracker and fetch birth counts from the repository.

## 4. Lessons Learned & Technical Debt
- **Performance Risk**: The `agent_states` table only has an index on `time`. The `get_birth_counts` query uses a `NOT IN` subquery which works well for small-to-medium datasets but may degrade performance as the simulation grows (O(N*M)).
- **Debt Item (TD-XXX)**: Add an index on `agent_states(agent_id, time)` or `agent_states(agent_id)` to optimize agent existence checks.
- **Metric Definitions**: The "Birth" definition is "Net New Survivors". Agents born and died within the same window (e.g., 5 ticks) are not counted. This mirrors the "Death" logic (Agents present at start, gone at end) but omits high-frequency churn. This is acceptable for a "Watchtower" (Macro) view but might be insufficient for detailed demographic debugging.
