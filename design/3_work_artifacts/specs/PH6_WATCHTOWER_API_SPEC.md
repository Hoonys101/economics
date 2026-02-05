# API Specification: The Watchtower [PH6-WT-API-001]

This document defines the "How" of technical communication between the Python Backend and Next.js Frontend.

---

## 1. Request Protocol (Watchtower Commands)
The Frontend sends commands via the WebSocket to control the simulation or fetch specific data.

| Command | Action | Payload Example |
|:---|:---|:---|
| `GET_SNAPSHOT` | Fetch the current world state. | `{ "cmd": "GET_SNAPSHOT" }` |
| `CHANGE_SCENARIO` | Force-switch the active economic paradox. | `{ "cmd": "CHANGE_SCENARIO", "params": { "scenario": "MALTHUSIAN" } }` |
| `DRILL_DOWN` | Fetch filtered data for a specific group. | `{ "cmd": "DRILL_DOWN", "params": { "group": "LOWER_QUINTILE" } }` |
| `PAUSE_RESUME` | Toggle simulation execution. | `{ "cmd": "PAUSE_RESUME" }` |

---

## 2. Response Protocol (The Watchtower Snapshot)
The Backend broadcasts this DTO every 1s (throttled) or upon request.

### 📍 Sheet: Global Header (HUD)
**Slot**: `TOP_NAV_HUD`
- `tick`: `int`
- `status`: `'RUNNING' | 'PAUSED' | 'EMERGENCY'`
- `integrity`: `m2_leak: float` (Critical Alert if > 0)

### 📍 Sheet: Overview Page
**Slot**: `OVERVIEW_MAIN`
- `vitals`: `gdp: float, cpi: float, unemploy: float, gini: float`
- `active_scenario`: `string` (e.g., "SCENARIO_B_LIQUIDITY_TRAP")
- `markers`: `List[{ "tick": int, "label": string }]`

### 📍 Sheet: Finance Page
**Slot**: `FINANCE_CORRIDOR`
- `rates`: `{ "base": float, "call": float, "loan": float, "savings": float }`
- `liquidity`: `{ "m0": float, "m1": float, "m2": float, "velocity": float }`

### 📍 Sheet: Politics Page
**Slot**: `POLITICS_GAUGES`
- `approval`: `{ "total": float, "low": float, "high": float }`
- `fiscal`: `{ "revenue": float, "welfare": float, "debt_ratio": float }`

### 📍 Sheet: Population Page
**Slot**: `POPULATION_CENSUS`
- `distribution`: `{ "q1": float, "q2": float, "q3": float, "q4": float, "q5": float }` (Asset distribution)
- `vitality`: `{ "birth": float, "death": float }`

---

## 3. Component-API Data Structures (TypeScript)

```typescript
type WatchtowerStatus = 'RUNNING' | 'PAUSED' | 'EMERGENCY';

interface WatchtowerSnapshot {
  tick: number;
  status: WatchtowerStatus;
  integrity: { m2_leak: number; fps: number; };
  macro: { gdp: number; cpi: number; unemploy: number; gini: number; };
  finance: {
    rates: { base: number; call: number; loan: number; savings: number; };
    supply: { m0: number; m1: number; m2: number; velocity: number; };
  };
  politics: {
    approval: { total: number; low: number; high: number; };
    fiscal: { revenue: number; welfare: number; debt: number; };
  };
  population: {
    active_count: number;
    metrics: { birth: number; death: number; };
  };
}
```

---

## 4. Confirmation Gate
**Golden Samples** for each page will be generated immediately based on this spec.
Next Step (Step 3) will commence simultaneous coding.
