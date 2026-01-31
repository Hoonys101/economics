# Refactor Phases and Government Agent

## Overview
This refactoring mission focuses on reducing bloating in `simulation/phases.py` and `simulation/agents/government.py` by extracting utility functions and components.

## Technical Debt & Insights

### `simulation/phases.py`
*   **Bloating:** The file contains multiple phase classes and a large `prepare_market_data` function, making it hard to navigate.
*   **Mixed Responsibilities:** `prepare_market_data` handles data aggregation, fallback logic, and even some calculation (e.g., debt burden).
*   **Legacy Code:** `Phase1_Decision` contains legacy signal construction logic that could be modularized.

### `simulation/agents/government.py`
*   **God Object:** The `Government` class handles taxation, welfare, infrastructure, elections, and sensory updates directly.
*   **Magic Numbers:** Several constants (e.g., `5000.0` for infrastructure cost, `0.02` for wealth tax) are hardcoded within methods.
*   **Coupling:** The class is tightly coupled with `TaxationSystem`, `FiscalPolicyManager`, and `MinistryOfEducation`, but also implements significant logic itself (welfare, infrastructure).

## Refactoring Strategy
1.  **Extract `prepare_market_data`:** Move this utility to `simulation/orchestration/utils.py` to declutter `phases.py` and allow cleaner imports.
2.  **Componentize Government:**
    *   **Welfare:** Extract `run_welfare_check` and related support logic to `WelfareManager`.
    *   **Infrastructure:** Extract `invest_infrastructure` to `InfrastructureManager`.
    *   **Constants:** centralized in `modules/government/constants.py`.

## Verification
*   Existing unit and integration tests must pass.
*   `test_government.py` and `test_engine.py` are critical.
