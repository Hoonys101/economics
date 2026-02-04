# Trace Leak Fix & Tech Debt Report

## Mission: TRACE-LEAK-FIX
**Date:** 2026-02-04
**Agent:** Jules

## Overview
The `trace_leak.py` script was failing due to missing configuration fields in `HouseholdConfigDTO`, specifically `survival_need_death_ticks_threshold`. This field was introduced in the `SocialComponent` refactoring but was not propagated to the DTO or the configuration loader.

## Technical Debt Detected

### TD-001: Configuration Naming Inconsistency
*   **Description:** `SocialComponent` uses `survival_need_death_ticks_threshold`, while legacy code and config use `HOUSEHOLD_DEATH_TURNS_THRESHOLD`.
*   **Impact:** Causes `AttributeError` and confusion about which parameter controls death logic.
*   **Resolution:** Added `survival_need_death_ticks_threshold` to `HouseholdConfigDTO` and mapped it in `config/__init__.py`.
*   **Recommendation:** Consolidate these into a single parameter in a future refactor.

### TD-002: Duplicate Config DTO Definitions
*   **Description:** `HouseholdConfigDTO` appears to be defined in `simulation/dtos/config_dtos.py` and possibly referenced/redefined in `modules/common/config/api.py`.
*   **Impact:** Potential for divergence if one is updated and the other isn't.
*   **Recommendation:** Unify config DTO definitions.

### TD-003: Trace Leak Script Fragility
*   **Description:** The script relies on strictly typed DTOs matching the dynamic `config` module, which makes it brittle to refactoring if DTOs aren't updated in lockstep.
*   **Impact:** Development friction when modifying configuration.

## Insights
*   The `SocialComponent` refactor seems to have proceeded without fully updating the configuration contracts.
*   Strict typing in DTOs (`create_config_dto`) is good for safety but requires discipline to keep `config/__init__.py` aligned.

## Actions Taken
1.  Verified the `NameError` / `AttributeError`.
2.  Added `survival_need_death_ticks_threshold` to `HouseholdConfigDTO`.
3.  Added corresponding constant to `config/__init__.py`.
4.  Verified `trace_leak.py` execution.
