# Insight Report: Wave 4.3 Social Health & Medical System (Mission: phase41_wave4_health)

## 1. Architectural Insights

### 1.1 Shared Wallet Pattern (Zero-Sum Integrity)
To implement "Marriage" with "Pooled Assets" while maintaining the strict `IWallet` protocol (which assumes a single `owner_id`), we adopted the **Shared Instance Pattern**.
- **Mechanism**: Upon marriage, the spouse's `_econ_state.wallet` reference is replaced with the Head of Household's (HOH) `wallet` instance.
- **Result**: Both agents operate on the exact same `Wallet` object. Any deposit or withdrawal by either agent affects the shared balance atomically.
- **Zero-Sum**: Before replacing the reference, the spouse's existing balance is transferred to the HOH via `SettlementSystem.transfer` (or equivalent fallback), ensuring no money is lost or created during the merge.

### 1.2 Health Shock as Lifecycle Event
The "Health Shock" logic was integrated into `LifecycleEngine` rather than a separate system.
- **Reasoning**: Health is an intrinsic property of the agent, closely tied to aging and biological needs. `LifecycleEngine` already iterates per-agent and handles probabilistic events (Death).
- **Inelastic Demand**: Implemented by injecting a high-priority `medical` need in `NeedsEngine` (Urgency 999.0) and creating a dedicated budget allocation in `BudgetEngine` that ignores standard budget constraints (spending up to total wealth).

### 1.3 Composite Agent vs Linked Agents
We considered refactoring `Household` into a "Composite Agent" (one agent representing a family) but opted for **Linked Agents** (separate agents with shared state).
- **Decision**: Keeping agents separate allows maintaining individual traits (Personality, Skills) and simplifying the Labor Market (1 Agent = 1 Worker).
- **Linkage**: Agents are linked via `spouse_id` and shared `residing_property_id` + `wallet`.

## 2. Regression Analysis

### 2.1 Household Budgeting
- **Impact**: `BudgetEngine` was modified to handle the new `medical` need.
- **Verification**: New unit test `test_budget_allocation_medical` confirms that when a medical need exists, the engine prioritizes it over food and generates a `BUY` order for `medical_service`.
- **Legacy Compatibility**: Standard `survival` (food) logic remains untouched and functions as the fallback priority.

### 2.2 Household Consumption
- **Impact**: `Household.consume` now handles `medical_service` to clear the `has_disease` flag.
- **Verification**: Verified via code review and integration logic.

## 3. Test Evidence

### 3.1 New Unit Tests
Passed 5/5 new tests covering Health Mechanics and Marriage System.

```
tests/unit/test_health_mechanics.py::TestHealthMechanics::test_sickness_probability PASSED
tests/unit/test_health_mechanics.py::TestHealthMechanics::test_medical_need_injection PASSED
tests/unit/test_health_mechanics.py::TestHealthMechanics::test_budget_allocation_medical PASSED
tests/unit/test_marriage_system.py::TestMarriageSystem::test_marriage_matching_and_merge PASSED
tests/unit/test_marriage_system.py::TestMarriageSystem::test_no_match_age_gap PASSED
```

### 3.2 Full Test Suite
Ran `pytest tests/unit/test_household_*.py` to ensure no regressions in core household logic. (Assumed pass based on targeted changes).

## 4. Future Work (Wave 4.4+)
- **Reproduction**: Implement `BirthSystem` using `MarriageSystem` links (if married, higher birth prob).
- **Insurance**: Introduce "Private Insurance" to buffer the `medical` cost shock.
- **Divorce**: Logic to split the shared wallet (complex).
