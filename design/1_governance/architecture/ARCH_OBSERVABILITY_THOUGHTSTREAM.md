# Architecture: Observability & ThoughtStream (W-0)

**Version**: 1.0 (2026-01-30)
**Status**: APPROVED

---

## 1. Philosophy: "Glass Box" Simulation
We move from **Symptomatic Treatment** (fixing bugs as they appear) to **Root Cause Analysis** (understanding *why* agents fail to act).
The simulation engine must be transparent, exposing not just *what happened* (Transactions), but *what failed to happen* (Rejected Intents) and *why* (Reasoning).

## 2. Core Architecture: The "Observe-Buffer-Flush" Pattern

To achieve high-performance logging without blocking the CPU-intensive simulation loop, we decouple **Observation** from **Persistance**.

```mermaid
graph LR
    subgraph Simulation Loop [High Speed CPU]
        A[Agent Decision] -->|Log Thought| Buffer[In-Memory Buffer]
        M[Market Match] -->|Log Transaction| Buffer
        S[State Change] -->|Log Snapshot| Buffer
    end

    subgraph I/O Operations [Batch Write]
        Buffer -->|Tick End Trigger| Writer[SimulationLogger]
        Writer -->|Bulk Insert + WAL| DB[(SQLite / WAL)]
    end

    style Buffer fill:#ffcc00,stroke:#333
    style DB fill:#99ccff,stroke:#333
```

### 2.1. Key Components

#### A. `SimulationLogger` (The Batch Writer)
- **Responsibility**: managing the in-memory buffer and executing high-performance batch writes.
- **Mechanism**:
  - **Buffer**: `List[LogEntry]`.
  - **Flush**: Executes `executemany` inside a single SQL transaction at the end of each tick.
  - **Mode**: Uses SQLite `WAL` (Write-Ahead Logging) for non-blocking reads/writes.

#### B. `ThoughtProbe` (The Why-Sensor)
- **Responsibility**: capturing the decision-making context of agents *in situ*.
- **Data Point**: "I wanted to buy food (Intent), but I didn't (Outcome) because the price was too high (Reason)."
- **Sampling**:
  - **Whale Tracking**: 100% logging for top 1% wealthy agents.
  - **Crisis Mode**: 100% logging when GDP=0 or Volatility > Threshold.
  - **Random Sample**: 5% logging for general population.

#### C. `SnapshotManager` (The World State)
- **Responsibility**: capturing a serialized view of the world for rewind/replay analysis.
- **Granularity**: Tick-level aggregates (Macro) + Entity-level snapshots (Micro).

## 3. Data Schema

### 3.1. `agent_thoughts`
Captures the "Consciousness Stream" of agents.
- `tick` (INT)
- `agent_id` (TEXT)
- `action_type` (TEXT): e.g., `CONSUME`, `PRODUCE`, `INVEST`.
- `decision` (TEXT): `COMMIT` or `REJECT`.
- `reason` (TEXT): e.g., `INSOLVENT`, `LOW_UTILITY`, `NO_INVENTORY`.
- `context_data` (JSON): e.g., `{"cash": 10.0, "price": 50.0, "needs": 0.9}`.

### 3.2. `tick_snapshots`
Captures the macro-state to correlate thoughts with reality.
- `tick` (INT)
- `gdp_nominal` (REAL)
- `total_money_supply` (REAL)
- `transaction_velocity` (REAL)

## 4. Integration Points
- **Household**: `decide_consumption`, `decide_labor`.
- **Firm**: `decide_production`, `decide_pricing`.
- **Market**: `match_orders` (record failed matches).
