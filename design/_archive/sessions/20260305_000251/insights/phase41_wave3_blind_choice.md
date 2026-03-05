# Mission Insight Report: Phase 4.1 - Wave 3.2: Blind Major Choice & Sunk Costs

**Mission Key**: `phase41_wave3_blind_choice`
**Date**: 2026-02-23
**Author**: Jules (AI Agent)

---

## 1. Architectural Insights

### Major Choice Logic Placement
- **Decision**: Implemented "Blind Major Choice" logic within `SystemEffectsManager._apply_education_upgrade`.
- **Rationale**: The `MinistryOfEducation` triggers the upgrade via a transactional effect (`EDUCATION_UPGRADE`). `SystemEffectsManager` is responsible for applying this effect. By placing the major choice logic here, we ensure it happens atomically with the education level upgrade, regardless of the transaction source (grant, scholarship, or self-funded).
- **Protocol Purity**: This respects the separation of concerns. The `Ministry` handles the financial transaction and policy eligibility, while the `SystemEffectsManager` handles the state mutation resulting from the transaction.

### "Blind Choice" Implementation
- **Mechanism**: Random selection from available specialized majors (excluding "GENERAL").
- **Constraint**: Only applies when `education_level` increases to 1 (or higher) AND the current major is "GENERAL" or `None`.
- **Config Dependency**: Majors are retrieved dynamically from `config_module.LABOR_MARKET["majors"]`, ensuring flexibility.

### "Sunk Costs" Implementation
- **Mechanism**: Implicitly enforced by the condition `if (current_major == "GENERAL" or current_major is None)`. If an agent already has a specialized major (e.g., from a previous level), the logic skips reassignment, effectively treating the prior choice as a sunk cost that cannot be changed during further education upgrades.

## 2. Regression Analysis

- **Affected Components**: `SystemEffectsManager`, `MinistryOfEducation` (indirectly).
- **Risk Assessment**: Low. The change is additive. Existing tests for `MinistryOfEducation` passed without modification because they primarily verify transaction generation, not the subsequent state effect details regarding majors.
- **Verification**:
    - Added `tests/unit/systems/test_system_effects_major_choice.py` to explicitly verify:
        1.  **Major Assignment**: Agents upgrading from Level 0 to 1 receive a non-GENERAL major.
        2.  **Sunk Cost**: Agents with an existing major (e.g., "TECHNOLOGY") retain it upon further upgrades.
    - Ran the full test suite (`pytest tests`) to ensure no regressions in other systems.

## 3. Test Evidence

### Full Test Suite Execution
```
================= 982 passed, 11 skipped, 2 warnings in 12.34s =================
```

### Reproduction Script Output (`tests/unit/systems/test_system_effects_major_choice.py`)
```
tests/unit/systems/test_system_effects_major_choice.py::TestSystemEffectsManagerMajorChoice::test_major_choice_on_education_upgrade
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.system_effects_manager:system_effects_manager.py:101 MAJOR_CHOICE | Household 101 selected major: MANUFACTURING
INFO     simulation.systems.system_effects_manager:system_effects_manager.py:106 EDUCATION_UPGRADE | Household 101 promoted to Level 1.
PASSED                                                                   [ 50%]
tests/unit/systems/test_system_effects_major_choice.py::TestSystemEffectsManagerMajorChoice::test_sunk_cost_major_choice
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.system_effects_manager:system_effects_manager.py:106 EDUCATION_UPGRADE | Household 102 promoted to Level 2.
PASSED                                                                   [100%]
```

### System Integrity
- **Zero-Sum**: No financial impact. Major choice is a metadata update.
- **Protocol**: Uses standard `Household` state access patterns.
