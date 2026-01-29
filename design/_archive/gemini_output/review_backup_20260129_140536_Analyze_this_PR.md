```markdown
## 🔍 Summary
This PR introduces new modules for economic stress testing: `modules/analysis` and `modules/simulation`. It defines DTOs and interfaces for shock injection and storm verification, and provides an implementation (`ShockInjector`, `StormVerifier`) along with a script to run a "Perfect Storm" stress test.

## 🚨 Critical Issues
*   **None identified.** No hardcoded API keys, passwords, external URLs, or absolute system paths. Zero-sum logic appears to be handled correctly within the context of the shock injector and verifier.

## ⚠️ Logic & Spec Gaps
1.  **Tight Coupling in `StormVerifier` and `ShockInjector`**: Both `StormVerifier` (L12-13, L20-21, L36, L47) and `ShockInjector` (L21, L34) directly access internal attributes of the `_simulation` object (e.g., `_simulation.central_bank`, `_simulation.government`, `_simulation.households`, `_simulation.firms`, `_simulation.config_module`). While DTOs are used for configuration, the `simulation: Any` type hint in `__init__` and `apply` methods bypasses type-checking for the simulation's structure. This creates a strong, implicit coupling between these modules and the simulation's internal implementation, making future refactoring of the simulation core more difficult and violating the API-driven development principle for inter-module communication.
2.  **Hardcoded `starvation_threshold` in `StormVerifier`**: In `modules/analysis/storm_verifier.py` (L40), `starvation_threshold` is hardcoded to `1.0`. Although there's a subsequent attempt to read from `self._simulation.config_module`, the initial hardcoded value and the comment indicate a potential inconsistency or an incomplete externalization of this parameter.
3.  **`main.py` Side Effects**: The comment in `scripts/run_stress_test_wo148.py` (L11-12) notes that `main.py` runs `setup_logging()` at the module level. Importing `create_simulation` from `main` directly can lead to unintended side effects or configuration overrides if `main.py` executes logic upon import. This indicates a potential architectural issue in `main.py` where it might be acting as both an entry point and a library module.
4.  **`sys.path.append(os.getcwd())` in Test Script**: While common in scripts, `scripts/run_stress_test_wo148.py` (L7) uses `sys.path.append(os.getcwd())`. For robust module imports, especially in a project structure like this, it's generally better to ensure modules are correctly discoverable via `PYTHONPATH` or project-specific setup tools to avoid potential import order issues or reliance on the current working directory.
5.  **`TD-118` Comment**: The comment `TD-118: Access inventory as dictionary` in `modules/analysis/storm_verifier.py` (L36) indicates outstanding technical debt or a pending change. This should ideally be resolved or formally tracked before merge.

## 💡 Suggestions
1.  **Define a `ISimulationObserver` Protocol**: To address the tight coupling, introduce a `Protocol` (e.g., `ISimulationState`) that the `simulation` object must adhere to. This protocol would expose only the necessary attributes and methods (`central_bank`, `government`, `households`, `firms`, `config_module`, `tracker`) that `StormVerifier` and `ShockInjector` require, ensuring a well-defined interface for interaction and improving modularity.
2.  **Externalize `starvation_threshold`**: Ensure `starvation_threshold` is consistently loaded from configuration (e.g., `VerificationConfigDTO` or a dedicated simulation config DTO) rather than being hardcoded or conditionally accessed.
3.  **Refactor `main.py`**: Separate the `create_simulation` function from any module-level side effects in `main.py`. Ideally, `main.py` should primarily serve as the application entry point and delegate setup/initialization to other modules or functions.
4.  **Parameterize Stress Test Configs**: For `scripts/run_stress_test_wo148.py`, consider loading shock and verification parameters from a YAML or JSON config file. This would make the stress test more flexible and reusable for different scenarios without modifying the script code.

## 🧠 Manual Update Proposal
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Update Content**:
    ```markdown
    # TD-118: Standardize Inventory Access
    - **Problem**: In `modules/analysis/storm_verifier.py`, there's a TODO comment indicating inventory access as a dictionary needs to be standardized. This suggests inconsistent inventory structures across agent types (e.g., Household, Firm).
    - **Impact**: Makes it difficult for analysis modules to reliably access inventory data, potentially leading to errors or inconsistent behavior.
    - **Proposed Solution**: Define a common interface or DTO for inventory access across all agents that hold inventory. Ensure all agents (Households, Firms, etc.) expose their inventory via this standardized mechanism (e.g., a dictionary, a dedicated Inventory object with well-defined methods).
    - **Priority**: Medium

    # TD-XXX: Loosen Coupling between Simulation Core and Observer/Injector Modules
    - **Problem**: `StormVerifier` and `ShockInjector` modules directly access internal implementation details of the `simulation` object (e.g., `_simulation.central_bank`, `_simulation.firms`).
    - **Impact**: Creates tight coupling, making it harder to refactor the simulation core without affecting these analysis/injection modules. Reduces modularity and testability.
    - **Proposed Solution**: Introduce `Protocol` interfaces (e.g., `ISimulationState` or `ISimulationAPI`) that the main `simulation` object implements. These interfaces should explicitly define the subset of attributes and methods that external modules like `StormVerifier` and `ShockInjector` are allowed to access. The `__init__` methods of `StormVerifier` and `ShockInjector` should then type-hint against these protocols.
    - **Priority**: High
    ```

## ✅ Verdict
**REQUEST CHANGES**
```
