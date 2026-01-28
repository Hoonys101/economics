# Work Order: WO-079 Config Automation v2

**Status:** READY
**Assigned to:** Jules (Implementer)
**Target Date:** 2026-01-16
**Related Spec:** [WO-079_Config_Automation_v2_Spec.md](../specs/WO-079_Config_Automation_v2.md)

## 1. Mission Objective
Implement a high-reliability, centralized configuration management system for the simulation engine and AI modules. This is a redo of the failed WO-079, focusing on architectural purity (Leaf Node) and maintaining test integrity.

## 2. Key Requirements
1.  **Leaf Node Interface**: Create `modules/common/config_manager/api.py` and `impl.py`. This module must have **ZERO** dependencies on other simulation modules (Bank, Firm, Engine, etc.).
2.  **Hybrid Loading**:
    *   Load all `.yaml` files from `config/` directory.
    *   Fall back to the legacy `config.py` module if a key is not found in YAML.
    *   YAML values always take precedence.
3.  **Test Compatibility Interface**: Implement `set_value_for_test(key, value)` to allow dynamic overrides during testing without modifying files.
4.  **Phased Implementation**:
    *   Step 1: Implement `ConfigManager`.
    *   Step 2: Inject `ConfigManager` into `Simulation` engine and `Bank`.
    *   Step 3: Migrate a subset of constants (e.g., Bank defaults) as a proof of concept.

## 3. Mandatory Constraints
- **NO Circular Dependencies**: If you encounter an import error, stop immediately and report.
- **PASS ALL TESTS**: Existing unit tests must pass. You must use `set_value_for_test` to mock configurations in tests that previously patched `config.py` directly.
- **Type Hinting**: All new functions must have full type hints and docstrings.

## 4. Verification Plan
- Run `pytest tests/test_config_manager.py` (to be created by you).
- Run existing bank tests: `pytest tests/test_bank.py` and ensure they still pass.
- Verify `engine.py` initialization with the new config manager.

---
**Approved by:** Antigravity (Chief Architect/PM)
