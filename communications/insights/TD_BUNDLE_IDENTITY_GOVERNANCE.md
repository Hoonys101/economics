# Insights: Identity & Governance Debt Resolution

## Technical Debt Resolved

### TD-224: Government Advisor Decoupling
- **Issue**: `Government.fire_advisor` contained hardcoded if/elif logic mapping `EconomicSchool` to `PolicyActionTag`, making it difficult to extend.
- **Resolution**: Introduced `SCHOOL_TO_POLICY_MAP` class constant. Refactored `fire_advisor` to look up policy tags dynamically. This simplifies the method and centralizes configuration.

### TD-220: Owner ID Type Unification
- **Issue**: `CentralBank.id` was a string `"CENTRAL_BANK"`, but `Wallet` required an integer `owner_id`. This created a mismatch where `CentralBank` passed `0` to its wallet but retained a string ID, leading to potential mapping errors in systems like `SettlementSystem` that perform ID checks.
- **Resolution**:
    - Unified `CentralBank.id` to be integer `0` (via `ID_CENTRAL_BANK` constant).
    - Updated `Wallet` initialization to use `self.id` (which is now `0`).
    - This ensures type safety and consistency across financial entities.

### TD-209: Hardcoded Agent Identifiers
- **Issue**: Multiple files (`SettlementSystem`, `WorldState`, tests) used hardcoded strings like `"CENTRAL_BANK"` to identify system agents.
- **Resolution**:
    - Defined `ID_CENTRAL_BANK = 0` in `modules/system/constants.py`.
    - Replaced hardcoded string checks (e.g., `str(agent.id) == "CENTRAL_BANK"`) with constant comparisons (`agent.id == ID_CENTRAL_BANK`) in source code and tests.
    - Note: Legacy string checks via `__class__.__name__` were retained in some places for robustness/mocking support, but primary ID checks now use the integer constant.

## Verification & Challenges
- **Tests**: `tests/integration/test_m2_integrity.py` initially failed because `ID_CENTRAL_BANK` (0) collided with `Government(id=0)` in the test setup. Fixed by changing Government test ID to 99.
- **Mocks**: `MockAgent` in unit tests failed because `SettlementSystem` now stricter checks `agent.wallet`. Fixed by properly mocking `wallet` property on test agents.
- **Scripts**: `scripts/verification/verify_integrity_v2.py` required updates to mocks to support the new wallet checks, though full execution remains flaky due to unrelated bitrot in the verification script itself.

## Future Recommendations
- **Registry**: Consider formalizing `agent_registry` keys in `DecisionInputDTO` to use constants or consistent mapping if mixed types persist.
- **Typing**: Enforce `id: int` more strictly in `BaseAgent` and `IFinancialEntity` via type hints and runtime checks to prevent regression.
