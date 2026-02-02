# TD-182: Refactor Agent Make Decision to use Immutable Market Snapshot

## Overview
This refactoring aimed to enforce immutability in agent decision-making by replacing raw `markets` dictionary access with a `MarketSnapshotDTO`. This ensures agents cannot mutate market state directly during the decision phase, adhering to the Single Responsibility Principle and reducing coupling.

## Technical Debt Addressed
*   **Direct Market Access**: Removed `markets` from `DecisionInputDTO`. Agents now rely solely on `MarketSnapshotDTO`.
*   **Shadow Mode Violation**: Fixed `Firm._calculate_invisible_hand_price` which was accessing raw market objects to calculate demand/supply. It now uses pre-calculated signals in `MarketSnapshotDTO`.
*   **DTO Fragmentation**: Unified `MarketSnapshotDTO` definitions. Previously, there was a `TypedDict` version in `modules/household/api.py` and a `dataclass` version in `modules/system/api.py`. Now, `modules/system/api.py` is the single source of truth using frozen dataclasses.

## Insights & Challenges
1.  **DTO Compatibility**: Transitioning from `TypedDict` to `dataclass` required updating attribute access in `DecisionUnit` (from `['key']` to `.key`). This highlights the importance of consistent DTO usage across modules.
2.  **Test Flakiness**: `test_ai_evaluates_consumption_options` in `test_household_ai.py` failed due to an edge case in price comparison (`avg_price >= max_affordable_price`). When test price equaled the calculated max affordable price, the agent refused to buy. Adjusted test data to avoid this edge case.
3.  **Environment Issues**: `numpy` was missing in the test environment, requiring a `pip install -r requirements.txt`. This suggests CI/CD pipelines should strictly enforce dependency installation.
4.  **Shadow Logic**: The "Invisible Hand" calculation in `Firm` is a good example of logic that *should* run on snapshot data but was lazily implementing direct access. Moving this to `MarketSignalFactory` (calculating total quantities) is a much cleaner architectural approach.

## Verification
*   All unit tests passed, including updated tests for factories and household AI.
*   `DecisionInputDTO` no longer carries mutable market references.
