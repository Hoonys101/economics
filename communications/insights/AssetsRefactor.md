# Insight Report: Assets Refactor (Mission: Replace 'self.cash' with 'self.wallet')

## Overview
This mission aimed to enforce the usage of `Wallet` API across all agents and ensure consistency in asset access, replacing the legacy `self.cash` float and unsafe `agent.assets` float usage.

## Technical Debt Identified
1.  **Implicit Float Assumption on Assets**:
    - Many subsystems (`Bank`, `ActionProposalEngine`, `System2Planner`, `EventSystem`, `DemographicManager`, `InheritanceHandler`) implicitly assumed `agent.assets` was a `float`.
    - With the introduction of `Wallet` and multi-currency support, `agent.assets` became a `Dict[CurrencyCode, float]`.
    - This caused potential `TypeError` (e.g., `dict >= float`) in logic that wasn't updated.

2.  **Duplicate Asset Access Logic**:
    - Various systems implemented ad-hoc checks for `assets` type (float vs dict) instead of using a standardized accessor or interface.

## Architectural Insights
1.  **Wallet as Single Source of Truth**:
    - The `Wallet` class (and `ICurrencyHolder` interface) provides a robust way to manage multi-currency balances.
    - All financial interactions should go through `SettlementSystem` or strict `Wallet` API calls, avoiding direct property access like `.assets`.

2.  **Interface Enforcement**:
    - Future refactoring should strictly enforce `ICurrencyHolder` on all agents involved in financial transactions to prevent regression.
    - `BaseAgent` and its subclasses now correctly expose `wallet`, but external consumers needed patching.

## Actions Taken
- Refactored `simulation/bank.py`, `simulation/decisions/action_proposal.py`, `simulation/ai/system2_planner.py`, `simulation/systems/handlers/inheritance_handler.py`, `simulation/systems/event_system.py`, `simulation/systems/demographic_manager.py`, `simulation/systems/generational_wealth_audit.py`, and `simulation/systems/persistence_manager.py`.
- Implemented safe asset extraction logic that prioritizes `agent.wallet.get_balance(DEFAULT_CURRENCY)`, falls back to `agent.assets.get(...)` (if dict), and `float(agent.assets)` (legacy).
- Verified fixes using a reproduction script `repro_assets_float.py`.

## Recommendations
- Deprecate `BaseAgent.assets` property entirely in a future phase to force usage of `wallet`.
- Introduce a static helper or service method for "get_primary_currency_balance(agent)" if `DEFAULT_CURRENCY` logic is ubiquitous, to reduce code duplication.
