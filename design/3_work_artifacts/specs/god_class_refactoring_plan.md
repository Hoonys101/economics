# Implementation Plan - TD-043/044/045: God Class Refactoring

This plan addresses the "God Class" anti-pattern in `Simulation`, `Household`, and `Firm` classes. These classes have excessive responsibilities, high coupling, and low cohesion, making maintenance and testing difficult.

## Goal Description
Decouple the monolithic "God Classes" into smaller, specialized components following the **Separation of Concerns (SoC)** principle and **Container/Component** pattern.

## User Review Required
> [!IMPORTANT]
> This is a high-risk structural refactoring. Backup of the codebase is recommended before proceeding.
> Major changes to `core_agents.py`, `firms.py`, and `engine.py` are expected.

## Proposed Changes

### 1. Simulation Refactoring (`simulation/engine.py`) - **Highest Priority**
-   **Problem**: `run_tick` is a procedural "God Method" managing incompatible domains.
-   **Action**: Extract logic into dedicated Systems.
    -   **`SocialSystem`**: Handles social rank calculations (`_update_social_ranks`).
    -   **`EventSystem`**: Handles chaos injection and scenario events (`_inject_chaos`).
    -   **`SensorySystem`**: Handles data aggregation for Government (`_update_sensory_modules`).
    -   **`CommerceSystem`**: Orchestrates consumption and leisure loops.
-   **New Structure**:
    -   `simulation/systems/social.py`
    -   `simulation/systems/events.py`
    -   `simulation/systems/sensory.py`

### 2. Household Refactoring (`simulation/core_agents.py`)
-   **Problem**: Low cohesion in `update_needs` and tight coupling to Market/Macro analysis.
-   **Action**:
    -   **Rename**: `update_needs` -> `run_lifecycle` to reflect actual behavior.
    -   **Extract**: Move market analysis logic (`choose_best_seller`, `shadow_wage`) to `MarketComponent`.
    -   **Decouple**: `make_decision` should return a `Plan` object, not execute trades directly.

### 3. Firm Refactoring (`modules/firms/firms.py`)
-   **Problem**: `Simulation` reaches into `Firm` internals (`ai_engine`) for learning updates.
-   **Action**:
    -   **Encapsulate**: Add `update_learning()` method to `Firm` public API.
    -   **Hide**: Make `decision_engine` and `ai_engine` private/protected.

## Verification Plan

### Automated Tests
-   **Unit Tests**: Create new tests for each extracted component (e.g., `test_biology.py`).
-   **Regression Tests**: Run existing `test_household.py` and `test_firms.py` to ensure no behavioral regression.
-   **Integration Test**: Run `main.py --ticks 50` to verify system stability after refactoring.

### Manual Verification
-   Inspect `audit` report post-refactoring to confirm reduced complexity and coupling.
