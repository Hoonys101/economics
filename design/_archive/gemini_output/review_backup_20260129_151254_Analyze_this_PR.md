## 🔍 Summary
This PR introduces new analysis and simulation shock injection capabilities, significantly improving modularity and type safety through the use of DTOs and Protocols (`api.py` files), addressing several technical debts (TD-149, TD-151, TD-118). A new stress test script `run_stress_test_wo148.py` is also added.

## 🚨 Critical Issues
None.

## ⚠️ Logic & Spec Gaps
1.  **Partial Resolution of TD-152**: In `modules/analysis/storm_verifier.py` (lines 35, 41, 62), `zlb_threshold`, `deficit_spending_threshold`, and `basic_food_key` still use hardcoded default values (`0.001`, `1.0`, `"basic_food"`) when accessing `self._config`. `VerificationConfigDTO` defines these as mandatory, so `self._config[...]` should be used directly without fallback defaults. Similarly, `starvation_threshold` (line 54) uses `getattr` with a hardcoded default (`1.0`) despite `IConfig` guaranteeing its presence. This weakens the configuration externalization and contract adherence.
2.  **`main.py` Import with Side Effects**: In `scripts/run_stress_test_wo148.py` (line 12), `from main import create_simulation` is used. The comment in the script itself notes that `main.py` runs `setup_logging()` at the module level. Importing `main.py` can lead to unexpected side effects or re-initialization of logging. `create_simulation` should ideally be refactored into a separate, side-effect-free utility module.

## 💡 Suggestions
1.  **Refactor `create_simulation`**: Move the `create_simulation` function from `main.py` to a dedicated `simulation/builder.py` or similar utility module. This will prevent `main.py`'s side effects from being triggered when importing just `create_simulation`.
2.  **Strict DTO Usage in `StormVerifier`**: Modify `modules/analysis/storm_verifier.py` to directly access values from `self._config` and `self._simulation.config_module` without providing hardcoded default values. This ensures that `VerificationConfigDTO` and `IConfig` are the single source of truth for these configuration parameters.

## 🧠 Manual Update Proposal
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
    *   Add a new section or update existing guidelines to clarify the process for adding entries to central ledgers like `TECH_DEBT_LEDGER.md`.
    *   Specify that new technical debt items should first be documented in a mission-specific insight file (e.g., `communications/insights/[Mission_Key].md`).
    *   Subsequently, a proposal can be made to incorporate them into the central ledgers, ensuring traceability and adherence to the "Decentralized Protocol" outlined in the `GEMINI.md` project guidelines.

## ✅ Verdict
REQUEST CHANGES
