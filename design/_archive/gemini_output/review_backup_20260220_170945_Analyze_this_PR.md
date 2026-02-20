# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
Implements **Phase 4: AI Perception Filters**, transitioning agents from "Perfect Information" to "**Bounded Rationality**".
- Introduces `PerceptionSystem` to distort market data based on an agent's `market_insight` score (Smart Money vs. Laggards vs. Lemons).
- Implements **Active Learning**: `market_insight` decays naturally but is boosted by high "Prediction Surprise" (TD-Error) or Education.
- Updates `FirmAI` and `HouseholdAI` to return `td_error` for this feedback loop.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
1.  **Deterministic Risk (`PerceptionSystem`)**:
    - `random.gauss(0, noise_level)` uses the global random state.
    - **Risk**: This compromises replayability if the global seed isn't strictly managed per-tick or if the system is multi-threaded.
    - **Fix**: Inject a seeded `random.Random` instance or `numpy.random.Generator` into `PerceptionSystem`.
2.  **String Heuristics (`_calculate_moving_average`)**:
    - `if ... and ("price" in key or "cost" in key):`
    - **Risk**: Implicit coupling. If a new market data field is named `value_index`, it won't be smoothed.
    - **Fix**: Define a list of smoothable keys in `MarketSnapshotDTO` metadata or configuration.
3.  **Magic Numbers**:
    - Thresholds (`0.8`, `0.3`), Decay (`0.001`), Boost (`0.05`), and Normalization (`1000.0`) are hardcoded in `perception_system.py` and agents.
    - **Risk**: Difficult to tune or optimize without code changes.

## 💡 Suggestions
1.  **Config Extraction**: Move the perception thresholds and decay rates to `GlobalRegistry` or a `PerceptionConfigDTO` to allow for runtime tuning and "God Mode" adjustments.
2.  **Telemetry**: Consider logging `market_insight` distribution (avg insight per tick) to `EconomicIndicatorTracker` to visualize the "Aggregate Alertness" of the economy.

## 🧠 Implementation Insight Evaluation
-   **Original Insight**:
    > "The introduction of PerceptionSystem marks a significant shift from 'Perfect Information' to 'Bounded Rationality'... Active Learning feedback loop where td_error (prediction surprise) directly boosts market_insight."
-   **Reviewer Evaluation**:
    -   **Valid**: The insight accurately reflects the architectural shift. The connection to "Austrian economics" (Alertness) provides excellent theoretical grounding.
    -   **Valuable**: Documenting the "Alertness" mechanism is crucial for understanding why some agents might behave irrationally (lagged data) vs. others (real-time).

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/1_governance/architecture/ARCH_AGENTS.md`

```markdown
### 3.4 Perception System (Cognitive Layer)
- **Concept**: Agents operate under **Bounded Rationality**. They do not see the raw `MarketSnapshot`; they perceive a distorted version based on their `market_insight` score (0.0 ~ 1.0).
- **Perception Tiers**:
  - **Smart Money (> 0.8)**: Perceives Real-Time, accurate market data.
  - **Laggards (> 0.3)**: Perceives a 3-Tick Moving Average (Smoothing).
  - **Lemons (<= 0.3)**: Perceives 5-Tick Latency + Gaussian Noise + Amplified Panic.
- **Active Learning Dynamics**:
  - **Decay**: Insight naturally decays (-0.001/tick) representing complacency.
  - **Boost**: High `TD-Error` (Surprise) or Education consumption boosts insight, simulating the "Alertness" mechanism where agents pay attention only when their predictions fail.
```

## ✅ Verdict
**APPROVE**