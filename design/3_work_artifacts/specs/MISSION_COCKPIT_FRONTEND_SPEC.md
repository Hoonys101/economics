File: design/3_work_artifacts/specs/MISSION_COCKPIT_FRONTEND.md
```markdown
# Spec: Cockpit 2.0 Frontend (React + WebSocket)

## 1. Executive Summary
This specification defines the frontend implementation for Cockpit 2.0, a "God Mode" dashboard for the economic simulation. It shifts from a polling-based architecture to a real-time event-driven model using WebSockets, strictly adhering to the `MISSION_COCKPIT_API_CONTRACT.md`. The UI is reorganized into four distinct layers to separate monitoring (System 1) from intervention (System 2).

## 2. Type Definitions (Strict Protocol)

The frontend **MUST** mirror the backend Pydantic models exactly. No camelCase conversion.

### 2.1. Target File: `frontend/src/types/dashboard.ts`

```typescript