# SPEC: TD-005 Halo Effect Liquidation

**Objective**: Liquidate technical debt TD-005 by removing the hardcoded `is_visionary` "Halo Effect" and replacing it with an emergent, brand-based resilience mechanism.

---

## 1. Problem Definition

-   **TD-005 (Hardcoded Halo Effect)**: The `is_visionary` flag in `simulation/firms.py` gives certain firms an unfair, hardcoded advantage by doubling their bankruptcy threshold. This violates market fairness principles and is redundant with the more sophisticated `BrandManager` system.

## 2. Implementation Plan

### Phase 1: Remove `is_visionary` Flag

1.  **Remove from Constructor**: Delete `is_visionary: bool = False` from the `Firm.__init__` signature in `simulation/firms.py`.
2.  **Remove from State**: Delete the `self.is_visionary = is_visionary` assignment within `__init__`.
3.  **Remove Logic Block**: Delete the entire `if self.is_visionary:` block that sets `self.consecutive_loss_ticks_for_bankruptcy_threshold`. The threshold will now be derived from the base config value for all firms initially.
4.  **Code Audit**: Perform a global search for `is_visionary` to ensure no other logic paths (e.g., in hiring or marketing) depend on this legacy flag. Remove any that are found.

### Phase 2: Implement Brand-Based Resilience

1.  **Modify Bankruptcy Check**: The primary logic will be in `simulation/components/finance_department.py`, within the `check_bankruptcy` method (or a similar method that tracks consecutive losses).
2.  **Introduce "Resilience" Logic**: The check for bankruptcy will be modified to account for brand strength.

    ```python
    # In simulation/components/finance_department.py
    # Inside a method like check_bankruptcy() or update_solvency()

    # 1. Get Brand Awareness from the firm's BrandManager
    # This requires the FinanceDepartment to have a reference to the firm.
    brand_awareness = self.firm.brand_manager.awareness

    # 2. Calculate resilience bonus ticks
    # The formula is tunable. Start with a simple linear mapping.
    # A resilience_factor of 0.05 means 20 points of awareness forgive 1 loss tick.
    resilience_factor = self.config.get("brand_resilience_factor", 0.05)
    resilience_ticks = int(brand_awareness * resilience_factor)

    # 3. Calculate effective loss ticks
    effective_loss_ticks = self.consecutive_loss_turns - resilience_ticks

    # 4. Check against threshold
    threshold = self.config.bankruptcy_consecutive_loss_threshold
    if effective_loss_ticks >= threshold:
        self.firm.is_bankrupt = True
        # ... bankruptcy logic
    ```

3.  **Configuration**: Add `brand_resilience_factor: 0.05` to the relevant configuration file (e.g., `economy_params.yaml`) to make the new mechanic tunable.

## 3. Verification Plan

1.  **Code Search**: After implementation, verify that no instances of the string `is_visionary` remain in the Python codebase.
2.  **Unit Test (`test_finance_department.py`)**:
    -   **Test Case 1 (Low Brand)**: Create a mock firm with low brand awareness (`awareness = 0`). Simulate consecutive losses and assert that the firm becomes bankrupt exactly at `config.bankruptcy_consecutive_loss_threshold`.
    -   **Test Case 2 (High Brand)**: Create a mock firm with high brand awareness (e.g., `awareness = 40`). Simulate consecutive losses. Assert that the firm survives *past* the default threshold and only goes bankrupt when `effective_loss_ticks` reaches the threshold.
3.  **Simulation Balance Test**:
    -   Run a baseline simulation for 1000 ticks with the old `is_visionary` code and record the total number of firm bankruptcies.
    -   Run the same simulation scenario with the new brand resilience code.
    -   Compare the total number of bankruptcies. The numbers should be in a similar range (e.g., within +/- 20%). If a mass extinction or mass survival event occurs, the `brand_resilience_factor` in the config must be tuned and the test re-run until the simulation is stable.

## 4. Risk & Impact Audit

-   **Critical Risk**: **Simulation Imbalance**. Removing the halo effect without a proper replacement could drastically increase bankruptcies and destabilize the economy.
    -   **Mitigation**: The proposed brand-based resilience mechanism is a direct, tunable replacement. The **Simulation Balance Test** is the key mitigation step. It is mandatory to run this test and analyze its output to ensure the new mechanic is properly calibrated before the change is considered complete.
-   **Architectural Impact**: This change is **positive**. It removes arbitrary, hardcoded rules and replaces them with an emergent property derived from a core simulation system (`BrandManager`), strengthening the integrity of the economic model.
