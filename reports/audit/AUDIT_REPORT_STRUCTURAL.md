# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit

**Date**: 2024-05-23
**Auditor**: Jules
**Scope**: `simulation/`, `modules/`, `tests/`
**Specification**: `design/3_work_artifacts/specs/AUDIT_SPEC_STRUCTURAL.md`

## 1. Executive Summary

The structural audit reveals a codebase in transition. While significant progress has been made towards a component-based architecture and DTO purity, two major "God Classes" (`Firm` and `Household`) persist as orchestrators with heavy internal logic. The core decision-making pipeline (`DecisionContext`, `BaseDecisionEngine`) is structurally sound and enforces DTO purity, but legacy patterns (e.g., side-effect execution within decision loops) remain in specific implementations like `Household.make_decision`. Dependencies between domains are clean, and the `TickOrchestrator` strictly enforces the simulation sequence.

## 2. God Class Analysis

Two primary classes exceed the 800-line threshold and orchestrate multiple domains, qualifying them as God Classes.

### 2.1. Firm (`simulation/firms.py`)
-   **Size**: ~1309 lines (physical file), ~840 lines (class definition).
-   **Responsibilities**: Orchestrates HR, Finance, Production, Sales, Asset Management, R&D, Brand, and Pricing.
-   **Architecture**: Implements a component-based pattern (`InventoryComponent`, `FinancialComponent`) but retains significant orchestration logic within the class methods (`produce`, `make_decision`, `generate_transactions`).
-   **Violation**: Acts as a central hub for 8+ distinct engines, violating Single Responsibility Principle.

### 2.2. Household (`simulation/core_agents.py`)
-   **Size**: ~1046 lines.
-   **Responsibilities**: Orchestrates Lifecycle, Needs, Social, Budget, Consumption, Belief, and Crisis management.
-   **Architecture**: Mixed state management. Uses internal DTOs (`_bio_state`, `_econ_state`, `_social_state`) but methods often manipulate this state directly or via mixins (`HouseholdStateAccessMixin`).
-   **Violation**: High complexity in `update_needs` and `make_decision` methods, coupling multiple domain engines.

## 3. Abstraction Leaks & Purity Violations

### 3.1. Clean Core Abstractions
The core decision API is structurally sound:
-   `DecisionContext` (`simulation/dtos/api.py`) strictly defines `state` as `Union[HouseholdStateDTO, FirmStateDTO]`.
-   `BaseDecisionEngine` (`simulation/decisions/base_decision_engine.py`) explicitly checks for DTO presence.
-   Tests (`tests/integration/test_purity_gate.py`) enforce that `DecisionContext` does not accept raw `household` or `firm` arguments.

### 3.2. Identified Leaks
-   **Housing System Injection**: `Household.make_decision` receives a raw `housing_system` object (typed as `Optional[Any]`) via `DecisionInputDTO`.
    ```python
    # simulation/core_agents.py
    if housing_action and input_dto.housing_system:
        self._execute_housing_action(housing_action, input_dto.housing_system)
    ```
    This constitutes a **Side-Effect Violation** and **Dependency Leak**. The decision phase should produce *intents* (e.g., a housing order), not execute them directly against a system object. This bypasses the standard `Transaction` and `Order` flow.

-   **Legacy Test Artifacts**: Grep searches revealed `DecisionContext` instantiations with `household=...` in `test_reports/full_test_results.txt`. These are confirmed to be artifacts of older test runs or misleading `repr` outputs, as the current code and `test_purity_gate.py` prohibit this.

## 4. Dependency & Module Structure

-   **Independence**: `modules/household/` and `modules/firm/` are cleanly separated with no direct cross-imports.
-   **Interfaces**: `SettlementSystem` (`simulation/systems/settlement_system.py`) correctly uses `IFinancialAgent` and `IFinancialEntity` protocols, decoupling it from concrete agent implementations.
-   **Legacy Imports**: `simulation/firms.py` imports `Household` but usage appears minimal/legacy.

## 5. Sequence Integrity

The `TickOrchestrator` (`simulation/orchestration/tick_orchestrator.py`) enforces the "Sacred Sequence":

1.  `Phase1_Decision` (Decisions)
2.  `Phase2_Matching` (Matching)
3.  `Phase3_Transaction` (Transactions)
4.  `Phase_Consumption` (Lifecycle/Consumption)
5.  `Phase5_PostSequence` (Cleanup)

*Note*: `Phase_Bankruptcy` and `Phase_HousingSaga` run before Matching. While technically "Lifecycle" events, their placement before matching allows liquidated assets to enter the market, which is a valid architectural decision for this simulation.

## 6. Recommendations

1.  **Decompose God Classes**: Continue extracting logic from `Firm` and `Household` into independent components or services. `Household` specifically needs a stricter component model similar to `Firm`.
2.  **Fix Housing Leak**: Refactor `Household.make_decision` to return a `HousingOrder` or `HousingIntent` instead of executing actions directly on `housing_system`. The execution should be handled by a dedicated system (e.g., `HousingSystem`) in a subsequent phase (e.g., `Phase3_Transaction` or a dedicated `Phase_Housing`).
3.  **Strict Typing**: Replace `Optional[Any]` for `housing_system` in `DecisionInputDTO` with a proper protocol or remove it entirely in favor of an intent-based pattern.
