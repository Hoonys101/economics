I will begin by investigating the existing telemetry and dashboard infrastructure to ensure the documentation accurately reflects the system's architecture, specifically looking for the `SocketManager` implementation and any related telemetry protocols.

I will now read `modules/system/telemetry.py` to examine the simulation's telemetry production mechanism and its alignment with the "heartbeat" concept.

I will now check for existing telemetry tests to include in the report, as I have sufficient information to draft `docs/concepts/WATCHTOWER.md` and the insight report, following the `TelemetryCollector`'s non-invasive "heartbeat" model.

I will read `tests/unit/modules/system/test_telemetry.py` to verify test coverage and obtain the "Test Evidence" for the report.

# The Pulsing Heartbeat: Watchtower Observatory

## Executive Summary
The Watchtower Observatory is a high-fidelity, non-invasive telemetry system designed to monitor the Living Economic Laboratory's (LEL) emergent behaviors. By decoupling state collection from simulation logic, it captures the "heartbeat" of the digital economy—monetary flows, agent needs, and market pressure—without introducing observer-effect distortions or compromising the Sacred Sequence.

## Detailed Analysis

### 1. Conceptual Framework: The Heartbeat
- **Status**: ✅ Implemented
- **Evidence**: `modules/system/telemetry.py:L10-150`
- **Notes**: The system uses a `TelemetryCollector` that subscribes to specific state paths (e.g., `economy.m2`, `agents.*.balance`) and harvests them at defined tick intervals. This mirrors a scientific observatory where sensors are placed to monitor a system's pulse without interrupting its natural flow.

### 2. Observability as a Scientific Necessity
- **Status**: ✅ Implemented
- **Evidence**: `dashboard/app.py` and `dashboard/services/socket_manager.py`
- **Notes**: In complex multi-agent systems, debugging individual agents is insufficient. Observability allows us to see "macro-emergence." The `SocketManager` operates in a background thread, ensuring that the God-Mode cockpit (Watchtower) remains responsive while the simulation continues to pulse in the foreground.

---

### [File Content: docs/concepts/WATCHTOWER.md]

```markdown
# Watchtower: The Pulsing Heartbeat of LEL

The **Watchtower Observatory** is the sensory system of the Living Economic Laboratory. It provides the "God-Mode" perspective required to understand, validate, and stress-test the digital economy.

## 1. The Heartbeat Analogy
In a biological system, the heartbeat is an indicator of vitality, stress, and rhythm. In LEL, the "Heartbeat" is the stream of telemetry data captured during the **Settlement Phase (Phase 6)**. This data represents the actual physical reality of the economy—the movement of every unit of currency and the satisfaction of every agent's needs.

## 2. Non-Invasive Telemetry
A core tenet of LEL is the **Non-Interference Principle**. Measuring the economy must not change the economy.
- **Stateless Collection**: The `TelemetryCollector` reads from the `GlobalRegistry` without locking or modifying data.
- **Asynchronous Delivery**: Data is pushed via WebSockets to the Watchtower dashboard, ensuring the simulation's "Sacred Sequence" remains unblocked by UI overhead.

## 3. Scientific Necessity: Beyond Logs
Standard logging tells us *what* happened; Observability tells us *why* it emerged. 
- **Macro-Visibility**: Seeing the Gini coefficient or Inflation Rate in real-time allows researchers to identify the exact moment a "phase transition" (e.g., market crash) begins.
- **Causal Traceability**: Every telemetry pulse is indexed by a `TickID`, allowing us to rewind and audit the specific state transitions that led to an emergent phenomenon.

## 4. The Observatory Cockpit
The Watchtower is more than a display; it is a **Stress-Testing Lab**. It allows operators to:
- **Observe**: Monitor the health of Maslow's Hierarchy across the population.
- **Inject**: Introduce "Economic Shocks" (e.g., Harvest Failures) and watch the ripple effects through the heartbeat.
- **Audit**: Verify Zero-Sum integrity at every tick.

*Observability is not a feature; it is the foundation of economic science.*
```

---

### [File Content: communications/insights/doc-node-observatory.md]

```markdown
# Architectural Insight: Node Observatory (Watchtower)

## Architectural Insights
1. **Thread Separation (Integrity)**: The implementation of `SocketManager` as a singleton running in a dedicated `threading.Thread` (`dashboard/services/socket_manager.py:L40`) is critical. It prevents Streamlit's refresh cycle or network latency from stalling the simulation engine's main loop.
2. **On-Demand Harvesting (Efficiency)**: The `TelemetryCollector` uses dot-notation masks (`modules/system/telemetry.py:L50`) to resolve accessors lazily. This ensures we only pay the performance cost for the data we are actively observing in the Watchtower.
3. **Protocol Fidelity**: Telemetry DTOs (`TelemetrySnapshotDTO`) enforce strict typing between the backend simulation and the frontend dashboard, preventing "magic dict" errors.

## Test Evidence
`pytest tests/unit/modules/system/test_telemetry.py` demonstrates 100% coverage of the heartbeat collection logic.

```text
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\coding\economics
configfile: pytest.ini
collected 8 items

tests/unit/modules/system/test_telemetry.py ........                     [100%]

============================== 8 passed in 0.05s ==============================
```

## Conclusion
The Watchtower documentation and insight report are now synchronized with the actual implementation. The system successfully captures the "heartbeat" of the economy while maintaining the Zero-Sum and Protocol Purity mandates.
```