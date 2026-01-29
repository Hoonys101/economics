# Work Order: WO-145 - Progressive Tax System

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** WO-144

## 1. Objective
Implement a progressive tax system as a core component of the government's fiscal policy, serving as an automatic stabilizer for the economy.

## 2. Implementation Plan

### Task A: Implement Fiscal Policy Manager
1.  In `modules/government/components/fiscal_policy_manager.py`, create the `FiscalPolicyManager` class that implements the `IFiscalPolicyManager` protocol.
2.  Implement the `determine_fiscal_stance` method. For the initial implementation, this method will return a static, default `FiscalPolicyDTO` as defined in the spec (e.g., 10%/25%/40% brackets). Dynamic adjustment is a future task.
3.  Implement the `calculate_tax_liability` method based on the pseudo-code provided in the specification. This method will calculate the total tax owed for a given income based on the progressive brackets in the `FiscalPolicyDTO`.

### Task B: Integration with Tax System
1.  The existing `TaxAgency` (or its post-refactoring equivalent) must be updated to use the new `FiscalPolicyManager`.
2.  The `GOVERNMENT_POLICY` phase in the `TickScheduler` must execute before the `TAX_COLLECTION_PHASE` to ensure the correct tax policy is available for the current tick.

## 3. Technical Constraints

- **Statelessness**: The `FiscalPolicyManager` MUST be stateless. All calculations should depend only on the arguments passed to its methods (e.g., `MarketSnapshotDTO`, `FiscalPolicyDTO`, `income`).
- **DTO Purity**: The manager must operate exclusively on DTOs for its inputs and outputs. It should not hold any internal state or directly access database repositories.
- **Unidirectional Data Flow**: The manager receives data and returns a result. It does not call out to other agents or managers directly.

## 4. Success Sign-off Criteria

- [ ] **Unit Tests Passed**: A new test file, `tests/modules/government/components/test_fiscal_policy_manager.py`, is created. It includes tests for `calculate_tax_liability` with multiple income scenarios.
- [ ] **Integration Verified**: An integration test confirms that the `TaxAgency` correctly uses the policy from `FiscalPolicyManager` to calculate and levy taxes.
- [ ] **Code Review**: A peer review confirms the implementation adheres to the stateless and DTO-purity constraints.
