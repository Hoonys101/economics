# PH9.2 Track B: Sensory System & Observation Purity

## 1. Problem Phenomenon
The `SensorySystem`, responsible for aggregating economic indicators for the Government, was directly accessing the internal state of agents. Specifically:
- It accessed `_bio_state.is_active` on Households.
- It accessed `_econ_state.assets` (checking for dict or float) on Households.
- It accessed `_social_state.approval_rating` on Households.

This violated the **encapsulation principle** and the **Separation of Concerns**. Agents' internal structure (DTOs like `_econ_state`) should be private. External systems should interact via defined interfaces. This coupling made refactoring agents difficult, as changing internal state structure would break the `SensorySystem`.

## 2. Root Cause Analysis
- **Lack of Interface:** There was no standard protocol for agents to expose their "observable" state to the world.
- **Leaky Abstractions:** The `SensorySystem` had knowledge of the specific implementation details of `Household` (e.g., that it has `_econ_state` and `_social_state` attributes).
- **Inconsistent Data Access:** The code had to handle `assets` being either a dictionary or a float, indicating a lack of standardized data contracts.

## 3. Solution Implementation Details
To resolve this, we implemented **Track B** of the Interface Purity reforms:

1.  **Defined `ISensoryDataProvider` Protocol:**
    - Located in `modules/simulation/api.py`.
    - Defines a single method: `get_sensory_snapshot() -> AgentSensorySnapshotDTO`.

2.  **Defined `AgentSensorySnapshotDTO`:**
    - A `TypedDict` containing strictly typed fields: `is_active`, `approval_rating`, `total_wealth`.
    - This serves as the Data Transfer Object between Agents and Observers.

3.  **Implemented Protocol in Agents:**
    - **`Household`:** Maps its internal `_bio_state`, `_social_state`, and `assets` to the DTO.
    - **`Firm`:** Maps `is_active` and `assets`. Returns `0.0` for `approval_rating` (neutral).
    - **`Government`:** Maps `approval_rating` and `assets`.

4.  **Refactored `SensorySystem`:**
    - Updated `generate_government_sensory_dto` to iterate over agents as `ISensoryDataProvider` objects.
    - Replaced all direct attribute access with `get_sensory_snapshot()`.
    - Removed fragile logic for handling `dict` vs `float` assets, as the DTO enforces a `float` contract for `total_wealth`.

## 4. Lessons Learned & Technical Debt
- **Legacy Debt in Verification Scripts:** The `scripts/audit_zero_sum.py` script failed with a `LIQUIDATION_ERROR` ("Firm 150 missing finance component"). This indicates that `LiquidationManager` is still relying on the deprecated `finance` component attribute, whereas `Firm` has moved to a Composition-based architecture (`finance_state` + `finance_engine`). This is unrelated to the Sensory refactor but blocked clean verification of the entire system.
- **Protocol Adoption:** Explicitly defining protocols like `ISensoryDataProvider` significantly improves code readability and safety. It allows for mocking in tests (as demonstrated in `tests/unit/test_sensory_purity.py`) without needing complex object graphs.
- **DTO vs. Dict:** Moving from raw dictionaries or direct attribute access to TypedDict/Dataclass DTOs enforces type safety and makes data flow explicit.

## 5. Verification
- **Unit Tests:** Created `tests/unit/test_sensory_purity.py` to verify that `SensorySystem` correctly aggregates data using the new protocol. Tests passed.
- **Purity Check:** Ran `scripts/verify_purity.py` which passed, confirming no architectural violations were introduced.
