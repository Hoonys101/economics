# Specification: PH6_THE_WATCHTOWER

## 1. Vision & Philosophy
"The Watchtower" is the central command center for the simulation. It shifts from static report auditing to real-time, flow-based observability.

### Hierarchical Design
- **HUD (Vitals)**: Critical stats (GDP, M2 Leak) always visible.
- **Contextual Pages**: Deep dives into Finance, Politics, and System performance.

## 2. Backend Architecture (Python/FastAPI)

### 2.1 Communication Protocol
- **Transport**: WebSocket (`/ws/live`).
- **Throttling**: Send updates every 1.0s or 10 ticks (whichever is slower) to prevent frontend saturation.
- **Payload**: JSON-encoded `TheWatchtowerSnapshotDTO`.

### 2.2 Data Aggregation (`DashboardService`)
- Collects raw data from `WorldState`.
- Computes 100-tick moving averages for GDP and Inflation.
- Maps `SystemEvents` to a displayable event log.

## 3. Frontend Architecture (Next.js)

### 3.1 Stack
- **Next.js 14+**: App Router for routing and `layout.tsx` for global WebSocket management.
- **Zustand**: Minimalist global state for the simulation pulse.
- **Charts**: Recharts or Chart.js for time-series visualization.

### 3.2 Pages & Zones
- **Zone A (Vitals)**: Real-time HUD. M2 Leak != 0 triggers a visual emergency state.
- **Zone B (Financial)**: Interest rate corridors and money supply charts.
- **Zone C (Political)**: Social cohesion heatmaps and approval gauges.
- **Zone D (System)**: Real-time terminal log.

## 4. Pass/Fail Criteria (UX)
- WebSocket connection establishes within 2s of page load.
- UI remains responsive (60fps) during high-load 100-tick runs.
- Navigation between pages preserves the WebSocket state.
