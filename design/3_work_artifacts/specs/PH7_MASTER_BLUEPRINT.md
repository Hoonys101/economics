# Phase 7 Master Blueprint: The Solid State Era

## 1. Objective
Synchronize all hardening efforts into a single architectural "Solid State." This phase marks the transition from **Fixing the Engine** (Development) to **Tuning the Economy** (Simulation).

## 2. The Post-Mission Reality (Expected State)
After the completion of the three primary missions (TD-FIX-MEMORY-ATTR, PH7-A-PURITY, TD-263), the following systemic shifts will occur:

| Pillar | Before | After (Solid State) |
| :--- | :--- | :--- |
| **Stability** | `AttributeError` on startup; sporadic DB locks. | Clean startup; high-concurrency WAL-optimized database. |
| **Integrity** | Side-effect inventory mutations; "Magic" item creation. | Protocol-enforced transactions; Immutable Saga snapshots. |
| **Visibility** | Watchtower Offline; Blind spots in birth/death rates. | Real-time WebSocket HUD; Live economic indicators. |
| **Role** | Fixing bugs (Jules/Antigravity). | Running scenarios & Balancing (Gemini/User). |

## 3. High-Level Architectural Targets

### 🟢 Target A: Domain Isolation (The Purity Suture)
- **Goal**: Sever the direct link between "Business Logic" and "Agent State".
- **Mechanism**: `IInventoryHandler` Protocol and `SagaSnapshotDTO`.
- **Success Metric**: 0 instances of `agent.inventory = ...` or `agent.cash -= ...` outside the Registry/Saga kernel.

### 🔵 Target B: Observability Hardening (The Glass Box)
- **Goal**: Full visibility into individual agent decision-making streams.
- **Mechanism**: `ThoughtStream` instrumentation and high-frequency WebSocket broadcasting.
- **Success Metric**: Dashboard connectivity > 99% uptime during 1000-tick stress tests.

### 🔴 Target C: Economic Regularization (The Balance)
- **Goal**: Transition from "Survival" to "Equilibrium".
- **Mechanism**: Tuning `economy_params.yaml` based on Watchtower feedback.
- **Success Metric**: Survival rate > 80% with M2 drift < 0.0001 over 2000 ticks.

## 4. Execution Roadmap

### Track 1: Hardening (CURRENT)
- [x] PH7-B: Inventory Violation Audit (Gemini)
- [ ] PH7-A: Protocol Implementation (Jules)
- [ ] TD-FIX-MEMORY-ATTR: Startup Fix (Jules)
- [ ] TD-263: Watchtower Recovery (Jules)

### Track 2: Verification (NEXT)
- [ ] Integrity Audit: Run `trace_leak.py` with protocol enforcement.
- [ ] Stress Test: 1000-tick run with Watchtower recording.
- [ ] Purity Check: `mypy` and `grep` audit for legacy access.

### Track 3: Tuning (FUTURE)
- [ ] Scenario: "The Great Stabilizer" (Finding equilibrium).
- [ ] Report: Phase 7 Final Performance & Insight.

---
**"We build the box to see the light."** - Project Economics v2.5
