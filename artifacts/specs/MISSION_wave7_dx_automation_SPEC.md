# MISSION SPEC: wave7-dx-automation

## 🎯 Objective
Improve Developer Experience (DX) and system performance by addressing friction points in ops and systemic bottlenecks.

## 🛠️ Target Tech Debts
1. **TD-DX-AUTO-CRYSTAL (Medium)**: Crystallization Overhead
    - **Symptom**: Manual script/JSON execution is required to register Gemini missions into the registries.
    - **Goal**: Automate mission registration via a decorator, watcher, or auto-discovery mechanism in `jules-go`/`gemini-go`.
2. **TD-SYS-PERF-DEATH (Low)**: O(N) Rebuild in Death System
    - **Symptom**: `death_system.py` uses O(N) rebuild behavior for modifying `state.agents` dict upon agent death.
    - **Goal**: Optimize agent removal to use efficient localized deletion (e.g., `.pop()`) to avoid massive dictionary rebuilds during mass liquidation events.

## 📜 Instructions for Gemini
1. **Analyze**: Investigate the mission registration flow (`launcher.py`, `service.py`) and identify where automation can replace manual DB entries. Review `death_system.py` for dictionary handling logic.
2. **Plan**: Design an auto-discovery module for specs (`artifacts/specs/`) to automatically sync with the DB. Outline the localized dictionary operation needed in `death_system.py`.
3. **Spec Output**: Produce a precise Jules spec to implement the automation and performance fixes.
