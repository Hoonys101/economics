# Work Order: WO-146 - Monetary Policy & Taylor Rule

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** WO-144

## 1. Objective
Implement a Taylor Rule-based monetary policy to allow the government (acting as a central bank) to manage inflation and employment by adjusting a target interest rate.

## 2. Implementation Plan

### Task A: Implement Monetary Policy Manager
1.  In `modules/government/components/monetary_policy_manager.py`, create the `MonetaryPolicyManager` class that implements the `IMonetaryPolicyManager` protocol.
2.  Implement the `determine_monetary_stance` method. This method will calculate the new `target_interest_rate` based on the Taylor Rule formula and pseudo-code provided in the implementation specification.

### Task B: Integration with Financial Markets
1.  The `target_interest_rate` from the resulting `MonetaryPolicyDTO` must be made available to the financial system.
2.  The new `finance_manager.py` (from `TD-142`) and the `LoanMarket` will use this rate as the base for setting their own interest rates. The `GOVERNMENT_POLICY` phase must run before agents make financial decisions.

## 3. Technical Constraints

- **Statelessness**: The `MonetaryPolicyManager` MUST be stateless. Its calculations must depend solely on the `MarketSnapshotDTO` passed into its methods.
- **DTO Purity**: The manager must receive a `MarketSnapshotDTO` and return a `MonetaryPolicyDTO`. It must not interact directly with other components or repositories.
- **Adherence to Future Architecture**: The integration MUST target the new, decoupled `finance_manager.py` as defined in `GOD_FILE_DECOMPOSITION_SPEC.md`, not the current monolithic `CorporateManager`.

## 4. Success Sign-off Criteria

- [ ] **Unit Tests Passed**: A new test file, `tests/modules/government/components/test_monetary_policy_manager.py`, is created. It includes tests verifying the Taylor Rule calculation for various inflation/unemployment scenarios.
- [ ] **Integration Verified**: An integration test confirms that the `target_interest_rate` is correctly propagated to and used by the new financing modules.
- [ ] **Code Review**: A peer review confirms the implementation adheres to the statelessness constraint and correctly implements the Taylor Rule formula.
