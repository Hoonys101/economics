# UI Quality Analysis Report: Watchtower & Reporting System

## 1. Architectural Alignment Analysis
**[Reference: design/1_governance/platform_architecture.md]**

*   **Protocol-Centered Loose Coupling**: 
    *   **Status**: Partial Compliance. The system uses a DTO-based WebSocket protocol for communication, which aligns with the "System & Interface" domain. However, the hardcoding of WebSocket URLs and paths in the frontend store creates a brittle coupling between the infrastructure layer and the application logic.
*   **Traceability by Default**:
    *   **Status**: Non-Compliant. While the engine generates snapshots, the UI layer acts as a "dumb terminal" that only displays the current state. There is no local persistence or history buffer in the frontend to support the "Deep Dive Analytics" envisioned in the Roadmap (Phase 20.5).
*   **Arm the Tool, Do not be the Tool**:
    *   **Status**: Compliant. The Watchtower is correctly positioned as an observation and "God-Mode" control tool, delegating all state calculations to the "Stateless Engine" in the backend.

## 2. Maintenance & Structural Assessment
**[Reference: watchtower/src/store/useWatchtowerStore.ts]**

*   **Single Responsibility Principle (SRP) Violation**: The `useWatchtowerStore` is currently a "God Store." It manages the WebSocket connection lifecycle, reconnection logic, error handling, and the global application state. This makes the store difficult to test in isolation and increases the risk of side-effect-driven bugs.
*   **Encapsulation & Testing**: The direct instantiation of the `WebSocket` object within the store's methods prevents dependency injection. This makes unit testing impossible without global mocks, violating the project's "Testability" design mandate.
*   **Reconnection Logic**: The implementation uses a manual exponential backoff. While functional, it is tightly coupled to the store, making it unavailable for other potential socket connections (e.g., dedicated log streams).

## 3. Data Integrity & Contract Verification
**[Reference: simulation/dtos/watchtower.py]**

*   **Contract Fragility**: The Python backend defines `WatchtowerSnapshotDTO` with high precision. However, the TypeScript counterpart is manually maintained. There is no automated mechanism (e.g., `ts-rs`, JSON Schema generation) to ensure synchronization. Any change to nested structures like `PoliticsDTO` will cause silent runtime failures or undefined fields in the UI.
*   **Zero-Sum Integrity**: The UI correctly prioritizes `m2_leak` and `integrity` metrics (M2 Leak, FPS), which reflects the core "Financial Integrity" principles of the platform.

## 4. Technical Debt & Architectural Drift

*   **Roadmap Discrepancy**: The `ROADMAP.md` (Phase 20.5) mentions Streamlit for "Simulation Cockpit" scaffolding, but the current implementation uses Next.js/React. This represents an unrecorded architectural pivot that should be documented in an ADR (Architecture Decision Record).
*   **Reliability Gap**: `sendCommand` is fire-and-forget. In a high-latency or unstable network environment, the "God-Mode" user has no confirmation that a macro-control command (e.g., base rate change) was actually accepted or executed by the engine.
*   **Config Purity**: The fallback to `localhost:8000` violates the "Config DTO Purity" principle. Infrastructure endpoints should be injected via environment variables or a dedicated configuration service.

## 5. Strategic Improvement Proposals

1.  **Infrastructure Decoupling**: Extract WebSocket management into a dedicated `SocketClient` class or service. Use an event-driven approach where the store subscribes to updates, separating connection logic from state management.
2.  **Contract-First Schema Sync**: Implement a shared schema (JSON Schema or Protobuf) as the source of truth. Use code generation to produce both Python DTOs and TypeScript types to eliminate "contract drift."
3.  **Command-Response Acknowledgment**: Upgrade the `sendCommand` protocol to include a `correlationId`. The engine should respond with an acknowledgment or error DTO, allowing the UI to show success/failure feedback.
4.  **Local Snapshot Buffer**: Implement a ring-buffer or IndexedDB storage in the frontend to maintain a history of the last 100-500 ticks. This enables real-time sparklines and trend analysis without re-fetching historical data from the server.
5.  **Environment-Driven Discovery**: Remove hardcoded strings. Use a central `ConfigDTO` on the frontend that reads from `process.env` to determine backend endpoints and feature flags.

## 6. Mandatory Reporting & Insights
**[Jules Instruction]**

모든 Jules는 본 품질 분석 보고서에 명시된 기술 부채(특히 TS/Python DTO 불일치 및 Socket 결합 문제)를 해결하기 위한 구체적인 작업 계획을 `communications/insights/UI_STABILIZATION.md`에 기록하고, `TECH_DEBT_LEDGER.md`에 해당 항목을 신규 등록하십시오. 아키텍처적 지뢰(Architectural Landmines)로 식별된 'Command-Response 정합성 부재'에 대한 대응 방안이 포함되지 않은 미션은 승인되지 않습니다.