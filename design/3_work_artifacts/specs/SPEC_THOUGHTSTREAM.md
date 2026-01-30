# Technical Specification: ThoughtStream Implementation (W-1)

**Target System**: `simulation/db/` & `simulation/agents/`

## 1. Objective
Implement the low-latency observability layer ("ThoughtStream") to capture agent decision-making processes and high-resolution world states.

## 2. Infrastructure Layer (`simulation/db/`)

### 2.1. `SimulationLogger`
- **Path**: `simulation/db/logger.py` (New File)
- **Class**: `SimulationLogger`
- **Methods**:
  - `__init__(db_path)`: Connect with `PRAGMA journal_mode=WAL` and `synchronous=NORMAL`.
  - `log_thought(tick, agent_id, action, decision, reason, context)`: Append to `self.buffer`.
  - `log_snapshot(tick, snapshot_data)`: Append to `self.snapshot_buffer`.
  - `flush()`: Execute `INSERT` for all buffered items in a transaction.

### 2.2. Schema Updates (`simulation/db/schema.py`)
- Add table `agent_thoughts`:
  ```sql
  CREATE TABLE IF NOT EXISTS agent_thoughts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id INTEGER,
      tick INTEGER,
      agent_id TEXT,
      action_type TEXT,
      decision TEXT,
      reason TEXT,
      context_data JSON
  );
  CREATE INDEX idx_thoughts_tick ON agent_thoughts(tick);
  ```
- Add table `tick_snapshots`:
  ```sql
  CREATE TABLE IF NOT EXISTS tick_snapshots (
      tick INTEGER PRIMARY KEY,
      run_id INTEGER,
      gdp REAL,
      m2 REAL,
      cpi REAL,
      transaction_count INTEGER
  );
  ```

## 3. Probe Injection Layer (`simulation/core_agents.py`)

### 3.1. `Household.decide_consumption`
- **Goal**: Detect why consumption is zero.
- **Instrumentation**:
  - Before returning `0` (no consumption), check conditions:
    - If `cash < price`: Log `REASON="INSOLVENT"`.
    - If `utility < cost`: Log `REASON="LOW_UTILITY"`.
    - If `inventory > max`: Log `REASON="SATISFIED"`.
  - **Log Call**:
    ```python
    simulation.logger.log_thought(
        tick=self.simulation.time,
        agent_id=self.id,
        action="CONSUME_FOOD",
        decision="REJECT",
        reason="INSOLVENT",
        context={"cash": self.assets, "price": market_price}
    )
    ```

### 3.2. `Firm.decide_production`
- **Goal**: Detect why production halts.
- **Instrumentation**:
  - If `cash < wage_bill`: Log `REASON="LIQUIDITY_CRUNCH"`.
  - If `inventory > accumulated`: Log `REASON="OVERSTOCK"`.

## 4. Integration Logic (`simulation/engine.py`)

- **Initialization**: Initialize `SimulationLogger` in `Simulation.__init__`.
- **Loop**: Call `simulation.logger.flush()` at the very end of `run_tick()`.

## 5. Constraints & Performance
- **Zero-Blocking**: Logging methods must strictly append to list (O(1)). No IO during tick.
- **Fail-Safe**: DB errors during flush should be logged but NOT crash the simulation (unless critical).
- **Sampling**:
  - Implement a `should_log(agent_id)` check.
  - Default: Log 100% of failed acts for now (to debug Deadlock).

## 6. Verification
- Run a 50-tick simulation.
- Query SQLite:
  ```sql
  SELECT reason, count(*) FROM agent_thoughts WHERE decision='REJECT' GROUP BY reason;
  ```
- Success if reasons (e.g., "INSOLVENT") are populated.
