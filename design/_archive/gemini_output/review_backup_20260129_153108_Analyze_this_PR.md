**🔍 Summary**: This PR introduces a new stress testing framework (WO-148) with `ShockInjector` and `StormVerifier` modules, using API-driven DTOs and Protocols for enhanced modularity. It also refactors the `create_simulation` function from `main.py` to `utils/simulation_builder.py` and updates the technical debt ledger.

**🚨 Critical Issues**: None.

**⚠️ Logic & Spec Gaps**:
1.  **Inconsistent `STARVATION_THRESHOLD` Sourcing**:
    *   **File**: `modules/analysis/storm_verifier.py` (L59)
    *   **Description**: While `VerificationConfigDTO` is introduced (addressing TD-152), the `STARVATION_THRESHOLD` is still accessed from `self._simulation.config_module.STARVATION_THRESHOLD` (via `IConfig` protocol), not directly from `VerificationConfigDTO`. This partially resolves TD-152, but `StormVerifier` is not fully decoupled from the global `config` module for this parameter.
2.  **Internal `MarketSnapshot` Representation**:
    *   **File**: `simulation/engine.py` (L70) and `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (TD-151)
    *   **Description**: TD-151 addresses "Anonymous DTO in Simulation Engine" and suggests replacing an inner `MarketSnapshot` with `MarketSnapshotDTO`. While `Simulation.get_market_snapshot()` now returns `MarketSnapshotDTO`, the internal `_prepare_market_data` still returns a generic `Dict[str, Any]`. The DTO is used for the public interface but not internally for consistency.
3.  **Hardcoded Stress Test Parameters**:
    *   **File**: `scripts/run_stress_test_wo148.py` (L23-28 and L37-41)
    *   **Description**: Key stress test parameters (e.g., `NUM_HOUSEHOLDS`, `NUM_FIRMS`, `shock_start_tick`, `tfp_multiplier`, `max_starvation_rate`) are hardcoded directly within the script. For improved maintainability and flexibility, these should be moved to a dedicated configuration file (e.g., in `config/scenarios/`).

**💡 Suggestions**:
1.  **Refactor `STARVATION_THRESHOLD`**: Move `STARVATION_THRESHOLD` into the `VerificationConfigDTO` and modify `StormVerifier` to access it from there. This would fully address TD-152.
2.  **Unify Internal `MarketSnapshot`**: Adjust `simulation/engine.py`'s `_prepare_market_data` to return a `MarketSnapshotDTO` directly to ensure consistent data representation internally and externally, fully resolving TD-151.
3.  **Externalize Stress Test Config**: Create a YAML configuration file for the stress test parameters in `scripts/run_stress_test_wo148.py` and load them at runtime. This enhances configurability and reusability.

**🧠 Manual Update Proposal**:
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Update Content**:
    *   **TD-152**: Update the description to reflect that `basic_food_key` is now in `VerificationConfigDTO`, but `STARVATION_THRESHOLD` (and other related thresholds mentioned in the original TD-152 description, like ZLB and Deficit Spending) still need to be externalized to the DTO for full compliance.
    *   **TD-151**: Clarify that while `Simulation.get_market_snapshot()` now uses `MarketSnapshotDTO`, the internal `_prepare_market_data` still returns a generic dictionary, indicating the remaining scope of this technical debt.
    *   **New TD**: Add a new technical debt item to address the hardcoding of test parameters in `scripts/run_stress_test_wo148.py`, proposing their externalization to a configuration file.

**✅ Verdict**: **REQUEST CHANGES**
