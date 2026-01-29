🔍 **Summary**: This PR introduces a robust stress testing framework (WO-148) with a shock injector and a storm verifier. It includes significant refactoring of the simulation initialization logic, moving `create_simulation` from `main.py` to `utils/simulation_builder.py`. New DTOs and Protocols (`ISimulationState`, `IShockInjector`) are defined to improve modularity and decouple analysis modules from the simulation engine. Tech debt items are updated, reflecting resolved issues and tracking active ones.

---

🚨 **Critical Issues**: None. No API keys, passwords, external server addresses, or absolute paths were found hardcoded. Zero-sum integrity appears to be maintained as the changes focus on parameter injection and state verification rather than direct currency/resource creation/destruction.

---

⚠️ **Logic & Spec Gaps**:

*   **`main.py` - `create_simulation` Removal:** While the `create_simulation` function was successfully moved to `utils/simulation_builder.py`, the provided diff for `main.py` only shows the removal of the function and related imports. There is no corresponding addition of `from utils.simulation_builder import create_simulation` or the updated call site. Assuming this is part of a larger change not fully presented in this diff, but it's a potential gap if `main.py` is no longer runnable. *(Self-correction: Given the context of a "Git Diff," I must assume the diff accurately represents the change. The absence of the new import/call in `main.py` means the file, as presented after the diff, would be broken. This needs to be addressed.)*
*   **`StormReportDTO` - `volatility_metrics` Placeholder**: The `StormReportDTO` in `modules/analysis/api.py` includes `volatility_metrics: Dict[str, float]`, but its implementation in `storm_verifier.py` uses `{"TBD": 0.0}`. This indicates an incomplete feature where volatility metrics are yet to be defined or calculated. This is a functional gap, not a critical bug, but should be tracked.

---

💡 **Suggestions**:

1.  **Complete `main.py` Refactoring**: Ensure `main.py` correctly imports and utilizes the `create_simulation` function from `utils.simulation_builder.py`. This is essential for the application to function after the refactoring.
2.  **Volatilty Metrics Implementation**: Prioritize the implementation of meaningful `volatility_metrics` in `StormVerifier` to make the stress test report more comprehensive. This could be added as a new tech debt item if not already covered.
3.  **Refine `ISimulationState` for `config_module`**: The `IConfig` protocol for `config_module` in `modules/simulation/api.py` currently only specifies `STARVATION_THRESHOLD: float`. As `StormVerifier` requires more configuration parameters (e.g., `zlb_threshold`, `deficit_spending_threshold`, `basic_food_key`) via `VerificationConfigDTO`, it might be beneficial to either:
    *   Expand `IConfig` to include these, or
    *   Pass `VerificationConfigDTO` directly to `StormVerifier`'s `__init__` without relying on `ISimulationState.config_module` for all verifier-specific parameters. The current approach passes `VerificationConfigDTO` directly, which is good. The `IConfig` protocol on `ISimulationState` seems primarily for the `STARVATION_THRESHOLD` used in `config.py` itself. This seems acceptable given the direct passing of `VerificationConfigDTO`.

---

🧠 **Manual Update Proposal**:

*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Update Content**:
    *   Acknowledge the `main.py` refactoring into a new utility. If `main.py` still has an issue as described above, update `TD-151` to reflect the full scope of `create_simulation`'s migration and `ISimulationState` compliance.
    *   Add a new Tech Debt for the `volatility_metrics` placeholder:

    ```
    | **TD-XXX** | 2026-01-29 | **Incomplete Volatility Metrics in StormReportDTO** | Implement meaningful volatility metrics calculation in `StormVerifier` for `StormReportDTO` | Incomplete reporting / Limited analytical depth | **ACTIVE** |
    ```

---

✅ **Verdict**: REQUEST CHANGES (Due to the critical issue identified in `main.py` if the assumption about a missing import/call is correct. If `main.py` is indeed fixed as part of a broader change, then the verdict would be APPROVE with the other points as suggestions for future improvement).
