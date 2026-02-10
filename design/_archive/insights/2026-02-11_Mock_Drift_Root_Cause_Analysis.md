# Insight Report: Fix Residual Test Failures (Phase 29 & Liquidation)

## 1. Context & Root Cause
Recent architectural changes to support Multi-Currency (Phase 33) and Asset/Liability Management refactoring shifted the internal representation of agent assets from a simple `float` (total wealth) to a `dict` (wallet balances per currency).

This change propagated through the codebase but left several integration and system tests behind, specifically those relying on `MagicMock` objects for agents (`Household`, `Firm`, `PublicManager`).

### The "Peeling Onion" of Mocks
The failures manifested as a cascade of errors:
1.  **AttributeError**: `float` object has no attribute `get`.
    *   *Cause*: Tests mocked `agent.assets` or `agent.wallet.get_balance` as a `float`, but updated logic (e.g., `initializer.py`, `bootstrapper.py`) expected a `dict` to call `.get(DEFAULT_CURRENCY)`.
2.  **TypeError**: `argument of type 'float' is not iterable`.
    *   *Cause*: `PublicManager` attempted to update `last_tick_revenue` (initialized as `0.0` but accessed as a `dict`).
3.  **TypeError**: comparisons between `MagicMock` and `int`/`float`.
    *   *Cause*: Once the attribute errors were fixed, deep logic (e.g., `DecisionEngine`, `LifecycleManager`) accessed secondary attributes (`hr_state`, `finance_state`, `consecutive_loss_turns`) which were missing from the mocks, causing them to return new `MagicMock` objects instead of values.

## 2. Technical Debt Identified

### A. Mock Drift
The primary debt is the divergence between **Test Doubles (Mocks)** and **Production DTOs**.
*   **Issue**: Many tests manually construct mocks (`h = MagicMock(); h.assets = 1000`). This is fragile. When the `Household` class evolves (e.g., assets becomes a property delegating to `wallet`), these manual mocks fail silently or noisily.
*   **Resolution**: We patched the specific tests, but a systemic solution requires using **Factories** (e.g., `create_mock_household`) that enforce the current schema of the agent.

### B. Inconsistent State Access
*   **Issue**: Some legacy code/tests accessed `agent.assets` directly, while others used `agent.wallet.get_balance()`.
*   **Resolution**: The refactor to `dict` forced standardization, but tests were the last to know.
*   **Guideline**: Tests should prefer using the public interface (`agent.get_balance(currency)`) rather than inspecting private state (`_econ_state.assets`), making them resilient to internal structure changes.

### C. Logic/Test Mismatch in Demographics
*   **Issue**: `DemographicsComponent` logic checks probability `0.0-1.0`, but the test configuration provided `100.0` (10,000%), causing an implicit assumption failure or confusion in intent.
*   **Resolution**: Aligned test data with domain constraints (Probability must be $\le 1.0$).

## 3. Implementation Insights

### 1. Dictionary Initialization for Accumulators
In `PublicManager`, the `last_tick_revenue` accumulator was initialized as `0.0` but used as a dictionary.
*   **Lesson**: Type hints (`Dict[str, float]`) are not enough; runtime initialization must match.
*   **Fix**: `self.last_tick_revenue = {DEFAULT_CURRENCY: 0.0}`

### 2. Configurable Mocking
The `Firm` constructor now strictly requires `profit_history_ticks` to initialize its `deque`.
*   **Lesson**: When adding configuration-driven data structures (`deque(maxlen=...)`), `Mock` configuration objects must be updated to provide these integers, or the object instantiation will crash during test setup.

## 4. Recommendations
1.  **Adopt Golden Fixtures**: Move away from ad-hoc Mocks for complex agents. Use serialization-based "Golden Fixtures" (snapshots of real agents) to ensure tests run against realistic state structures.
2.  **Strict Typing for Mocks**: Use `spec=Household` (which we did) but ensure the spec is up-to-date.
3.  **Deprecate Direct Asset Access**: Enforce `ICurrencyHolder` interface usage in tests to abstract away the storage mechanism (float vs dict).
