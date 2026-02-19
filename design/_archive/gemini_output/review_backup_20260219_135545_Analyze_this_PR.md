# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
Refactored the Cockpit Frontend to version 2.0 Foundation. Introduced a **Dual-WebSocket Architecture** (Live Telemetry vs. Command Channel) to separate high-frequency reads from control writes. strict TypeScript DTOs now mirror Python dataclasses, and the backend (`server.py`) was updated to support Query Parameter authentication for browser WebSocket compatibility.

## 🚨 Critical Issues
*   None found.

## ⚠️ Logic & Spec Gaps
*   **Security (Low Severity)**: `frontend/src/services/socket.ts` defaults to `"default-god-token"` if the env var is missing. While acceptable for a local dev tool, ensure this fallback is removed or strictly warned against in production-like environments to prevent unauthorized command access.

## 💡 Suggestions
*   **Hardcoded Proxy Target**: `frontend/vite.config.ts` hardcodes `target: 'http://localhost:8000'`. Consider loading this from an environment variable (e.g., `VITE_API_TARGET`) to support running the frontend against a remote backend or a different local port.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "Authentication Update: The backend (`server.py`) was modified to accept the `X-GOD-MODE-TOKEN` via a query parameter (`?token=...`) ... This was necessary because standard browser `WebSocket` APIs do not support setting custom headers during the connection handshake."
*   **Reviewer Evaluation**:
    *   **Validity**: High. This is a well-known limitation of the browser `WebSocket` API. Using a query parameter is the standard workaround, although it exposes the token in server access logs (URL). Given this is an internal "God Mode" tool, the trade-off is acceptable.
    *   **Completeness**: The insight correctly identifies the architectural impact (Backend change driven by Frontend constraint).

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/HANDOVER.md`
*   **Draft Content**:
    ```markdown
    ### Cockpit 2.0 Architecture (2026-02-19)
    - **Dual-Channel Protocol**:
      - `/ws/live`: Read-only, high-frequency telemetry stream (Unauthenticated/Public Data).
      - `/ws/command`: Write-only, authenticated command dispatch (requires `?token=` or Header).
    - **Frontend Stack**: React + TypeScript + Vite.
    - **Type Safety**: strict DTO parity enforced via `frontend/src/types/*.ts`.
    ```

## ✅ Verdict
**APPROVE**