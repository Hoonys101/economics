# Implementation Plan: Task #6 - Maslow's Hierarchy & Education

**Target Goal**: Implement Maslowian needs gating for agent decision making and an Education system that improves offspring learning rates.

## 1. Config Updates (`config.py`)
- Add `MASLOW_SURVIVAL_THRESHOLD = 50.0`
- Add Education Constants: `EDUCATION_SENSITIVITY`, `BASE_LEARNING_RATE`, `MAX_LEARNING_RATE`, `LEARNING_EFFICIENCY`.
- Register `education_service` in `GOODS` dictionary with `is_service=True`.

## 2. Core Agent Updates (`simulation/core_agents.py`)
- **Household**:
    - Add `self.education_xp = 0.0` to `__init__`.
    - Modify `consume()` method:
        - Check if item is `education_service`.
        - If yes, increment `education_xp` and skip inventory addition.

## 3. AI Engine Updates (`simulation/ai/household_ai.py`)
- **Action Masking**:
    - In `decide_action_vector`:
    - Check if `current_needs['survival'] > MASLOW_SURVIVAL_THRESHOLD`.
    - If true, force aggressiveness for non-survival channels (social, improvement, investment) to `0.0`.
- **Inheritance Logic**:
    - Ensure `education_xp` is passed or used during mitosis.
    - Wait, the spec says "Mitosis Linkage (Child Learning Rate Bonus)".
    - This likely happens in `simulation/engine.py` (mitosis handling) or `simulation/ai/ai_manager.py` (when creating new AI).
    - Spec Section 5.1 says `Household.check_mitosis()` or `AITrainingManager.inherit_brain()`.
    - I will implement this in `inherit_brain` logic or where the new agent is initialized.

## 4. DB Schema Update (`simulation/db/schema.py`)
- Add `education_xp` column to `agent_states` table.
- Update `SimulationRepository` or `AgentStateViewModel` to include this field if necessary.

## 5. Testing Strategy
- **Unit Test**: `tests/test_maslow_education.py`
    - Test 1: **Maslow Gating**:
        - Set agent survival need high (>50).
        - Verify decision output has 0.0 aggressiveness for non-survival goods.
        - Set survival need low. Verify normal behavior.
    - Test 2: **Education Consumption**:
        - Simulate purchase of `education_service`.
        - Verify `education_xp` increases.
        - Verify item is not in inventory.
    - Test 3: **Inheritance Bonus**:
        - Create parent with high `education_xp`.
        - Trigger mitosis/inheritance.
        - Verify child's AI `learning_rate` (alpha) is higher than base.

## 6. Execution Steps
1.  **Config**: Update `config.py` (constants + goods).
2.  **Schema**: Update `schema.py` (add column).
3.  **Core**: Update `Household` class (init + consume).
4.  **AI**: Update `HouseholdAI` (masking) and `AIEngineRegistry` (inheritance).
5.  **Test**: Write and run `tests/test_maslow_education.py`.
6.  **Verify**: Run simulation for a few ticks and check DB for `education_xp` values.

## 7. Dependencies
- Depends on Phase 2 (Mitosis) code being present (it is).
- No new external libraries.
