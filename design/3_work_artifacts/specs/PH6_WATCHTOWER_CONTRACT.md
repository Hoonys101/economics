# API Contract: The Watchtower [PH6-WT-001]

This document serves as the official data contract between the **Python Backend (Simulation)** and the **Next.js Frontend (Command Center)**.

## 1. Protocol Specification
- **Endpoint**: `ws://localhost:8000/ws/live`
- **Format**: JSON (UTF-8)
- **Pulse Rate**: Variable (Default: 1.0s throttled or every 10 ticks)

---

## 2. Frontend Interface (TypeScript)

```typescript
export interface WatchtowerSnapshot {
  tick: number;
  timestamp: string; // ISO-8601
  system_integrity: {
    m2_leak: number; // Unit: Currency
    fps: number;    // Simulation speed
  };
  macro_economy: {
    gdp_growth: number;        // Percentage (%)
    inflation_rate: number;     // Percentage (%)
    unemployment_rate: number;  // Percentage (%)
    gini_coefficient: number;   // 0.0 - 1.0
  };
  monetary: {
    base_rate: number;      // Central Bank Rate (%)
    interbank_rate: number; // Market Call Rate (%)
    m2_supply: number;      // Total Money
    exchange_rates: Record<string, number>; // e.g., {"KRW": 1400.0}
  };
  politics: {
    party: 'RED' | 'BLUE' | 'NEUTRAL';
    approval_rating: number; // 0.0 - 1.0
    social_cohesion: number; // 0.0 - 1.0
    current_events: string[]; // List of significant tick events
  };
}
```

---

## 3. Field Definitions & Constraints

| Field | Type | Constraint | Description |
|:---|:---|:---|:---|
| `m2_leak` | `number` | `val == 0.0000` | **CRITICAL.** If non-zero, triggers Emergency HUD state. |
| `gdp_growth` | `number` | | Change vs Previous SMA (Simple Moving Average). |
| `base_rate` | `number` | `0.0 <= val` | Set by Central Bank policy. |
| `interbank_rate` | `number` | | Result of Bank AI matching in Call Market. |
| `party` | `string` | Enum | The current party in power (governance context). |

---

## 4. Error Handling & State Recovery
- **Connection Loss**: Frontend should attempt exponential backoff reconnection.
- **Payload Validation**: If a tick is skipped due to processing delay, the `tick` counter will jump; the frontend should update time-series charts accordingly.

---
**Approved by**: Antigravity (Team Lead)  
**Ref Schema**: `simulation/dtos/watchtower.py`
