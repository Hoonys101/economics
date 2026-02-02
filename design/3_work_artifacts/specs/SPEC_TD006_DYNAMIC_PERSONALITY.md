# SPEC: TD-006 Dynamic Household Personality

**Objective**: Liquidate technical debt TD-006 and support TD-162 by converting the `Household` agent's static personality into a dynamic trait that adapts to its economic circumstances.

---

## 1. Problem Definition

-   **TD-006 (Static Personality)**: `Household` personality is fixed at initialization, leading to unrealistic behavior where agents do not adapt their core motivations (e.g., a `MISER` remains a miser even when wealthy).
-   **TD-162 (Bloated God Class)**: The `Household` class is a "God Class" undergoing decomposition. New logic must be placed in the correct sub-components, not added to the `Household` facade.

## 2. Implementation Plan

### Phase 1: Enable Dynamic Personality

1.  **Remove `__init__` Parameter**: Delete the `personality: Personality` parameter from the `Household.__init__` method signature in `simulation/core_agents.py`.
2.  **Default Personality**: Set a neutral default personality (e.g., `Personality.BALANCED`) inside `__init__` when initializing the `SocialStateDTO`.
3.  **Update Call Sites**: Find all `Household(...)` instantiation calls and remove the `personality` keyword argument. This will cause intentional compilation/runtime errors that will guide the refactoring.

### Phase 2: Implement Logic in `SocialComponent`

1.  **New Method**: Create a new method in `modules/household/social_component.py`:
    `update_dynamic_personality(social_state: SocialStateDTO, econ_state: EconStateDTO, macro_context: MacroFinancialContext) -> SocialStateDTO`
2.  **Call from `Household`**: This new method should be called once per tick, for example, from within `Household.update_needs`.
3.  **Personality Logic**: The core logic will reside in `update_dynamic_personality`.

    ```python
    # In modules/household/social_component.py

    def update_dynamic_personality(self, social_state: SocialStateDTO, econ_state: EconStateDTO, macro_context: MacroFinancialContext) -> SocialStateDTO:
        """Updates personality based on relative wealth."""

        # Use percentile from macro_context, which should be pre-calculated
        wealth_percentile = macro_context.wealth_percentiles.get(social_state.id, 0.5)

        new_personality = social_state.personality
        
        # Define thresholds in config
        status_seeker_threshold = self.config.personality_status_seeker_wealth_pct
        survival_mode_threshold = self.config.personality_survival_mode_wealth_pct

        if wealth_percentile >= status_seeker_threshold:
            new_personality = Personality.STATUS_SEEKER
        elif wealth_percentile <= survival_mode_threshold:
            # Assume SURVIVAL_MODE is a new Personality enum member
            new_personality = Personality.SURVIVAL_MODE 
        else:
            # Optional: Revert to a base or neutral personality
            # For now, we only change at the extremes.
            pass
        
        if new_personality != social_state.personality:
            social_state.personality = new_personality
            # IMPORTANT: Update desire weights to match the new personality
            social_state.desire_weights = self.config.desire_weights_map.get(new_personality.name)

        return social_state
    ```
4.  **Add `SURVIVAL_MODE`**: Add `SURVIVAL_MODE` to the `Personality` enum in `simulation/ai/enums.py`.
5.  **Configuration**: Add the thresholds and desire weights map to the configuration files.
    -   `personality_status_seeker_wealth_pct: 0.9` (Top 10%)
    -   `personality_survival_mode_wealth_pct: 0.2` (Bottom 20%)
    -   A `desire_weights_map` that links each personality name to its desire weight dictionary.

## 3. Verification Plan

1.  **Unit Test (`test_social_component.py`)**:
    -   **Test Case 1 (Status Seeker)**: Create state DTOs where the agent's wealth percentile in `macro_context` is `0.95`. Call `update_dynamic_personality` and assert that the returned `SocialStateDTO` has `personality = Personality.STATUS_SEEKER`.
    -   **Test Case 2 (Survival Mode)**: Create state DTOs where the agent's wealth percentile is `0.15`. Call the method and assert the personality becomes `Personality.SURVIVAL_MODE`.
    -   **Test Case 3 (No Change)**: Use a wealth percentile of `0.5` and assert the personality does not change from its initial state.
2.  **Integration Test**:
    -   Create a test scenario where a household's assets are manually increased over several ticks.
    -   In each tick, call `update_needs` (which triggers the personality update) and assert that the `household.personality` property changes from `BALANCED` to `STATUS_SEEKER` once its relative wealth crosses the configured threshold.
3.  **Call Site Audit**: The primary verification is to run the entire test suite. The build will fail at every location where `Household` is instantiated with the removed `personality` argument. Each of these failures must be fixed.

## 4. Risk & Impact Audit

-   **Critical Risk**: **Breaking Test and Scenario Setups**. Many existing tests rely on initializing households with a specific personality to create a predictable scenario. Removing the `__init__` argument will break all of them.
    -   **Mitigation**: This is an unavoidable and intended consequence of the refactoring. Test setups must be updated to reflect the new dynamic system. Instead of setting personality directly, tests must now **manipulate the economic state** to *induce* the desired personality.
    -   **Example Fix**:
        -   **Old**: `household = Household(..., personality=Personality.STATUS_SEEKER)`
        -   **New**:
            ```python
            household = Household(...)
            # Manually set high assets and a macro context to force the change
            household._econ_state.assets = 1_000_000
            mock_macro_context = MacroFinancialContext(wealth_percentiles={household.id: 0.95})
            household._social_state = household.social_component.update_dynamic_personality(household._social_state, household._econ_state, mock_macro_context)
            # Now the household is a STATUS_SEEKER for the test
            ```
-   **Architectural Impact**: **Positive**. This change resolves TD-006 and pushes the `Household` class further towards a clean, decomposed state (addressing TD-162) by correctly placing behavioral logic in the `SocialComponent`.
