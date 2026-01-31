```markdown
# Spec: Zero-Sum Integrity for Government Fiscal Operations
****

## 1. Overview & Problem Statement

The simulation suffers from a critical timing flaw where government deficit spending fails. The root cause, as identified in `design/audits/ROOT_CAUSE_PROFILE.md`, is an architectural mismatch:
1. **Asynchronous Financing**: Deficit financing (`issue_treasury_bonds`) creates deferred `Transaction` objects that are processed later in the tick.
2. **Synchronous Spending**: The corresponding expenditure (`invest_infrastructure`, `run_public_education`) attempts an *immediate* asset transfer before the funds from bond sales have settled.

This specification details a refactoring plan to synchronize these operations, ensuring fiscal integrity. The chosen solution is to make bond settlement immediate, aligning it with the existing direct settlement mechanism used for spending. This avoids the "Transaction Trap" and the risks associated with using the `TransactionProcessor` for internal government fund movements.

## 2. Proposed Architectural Changes

The core principle is to **unify all deficit-financed spending under a single, synchronous settlement pattern** using the `ISettlementSystem`, bypassing the deferred `TransactionProcessor`.

### 2.1. `modules.finance.api.IFinanceSystem` (Interface Change)

The `issue_treasury_bonds` method signature will be altered to reflect its new synchronous nature.

**Current (Asynchronous):**
```python
def issue_treasury_bonds(self, amount: float, current_tick: int) -> Tuple[List[Bond], List[Transaction]]:
 ...
```

**Proposed (Synchronous):**
```python
def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: float, current_tick: int) -> bool:
 """
 Issues bonds and attempts to settle them immediately.
 Directly transfers funds from buyers to the issuer's account via the SettlementSystem.
 Returns True on full success, False on failure.
 """
 ...
```
* **Rationale**: The method no longer returns `Transaction` objects. It returns a simple boolean indicating whether the full `amount_to_raise` was successfully secured and deposited into the `issuer`'s account.

### 2.2. `modules.finance.finance_system.FinanceSystem` (Implementation Change)

The implementation of `issue_treasury_bonds_synchronous` will be responsible for the entire synchronous sale process.

**Pseudo-code:**
```python
def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: float, current_tick: int) -> bool:
 # 1. Find potential buyers (e.g., banks, wealthy households) with available assets.
 potential_buyers = self.find_bond_buyers()

 # 2. Iterate through buyers and perform direct transfers.
 amount_raised = 0.0
 for buyer in potential_buyers:
 if amount_raised >= amount_to_raise:
 break

 purchase_amount = min(buyer.assets * 0.1, amount_to_raise - amount_raised)
 if purchase_amount <= 0:
 continue

 # 3. Use SettlementSystem for a direct, immediate transfer.
 transfer_success = self.settlement_system.transfer(
 sender=buyer,
 recipient=issuer,
 amount=purchase_amount,
 description=f"Bond Purchase from {buyer.id}"
 )

 # 4. If transfer succeeds, create Bond record and update amount raised.
 if transfer_success:
 self.create_bond_asset(owner=buyer, face_value=purchase_amount, tick=current_tick)
 amount_raised += purchase_amount

 # 5. Return True only if the entire required amount was raised.
 if amount_raised >= amount_to_raise:
 logger.info(f"Successfully raised {amount_raised:.2f} for {issuer.id} via synchronous bond sale.")
 return True
 else:
 logger.warning(f"Failed to raise full amount. Needed {amount_to_raise:.2f}, got {amount_raised:.2f}.")
 # CRITICAL: Logic to handle partial funding (e.g., returning the partial funds) should be considered.
 # For now, we assume failure means the operation is aborted.
 # A potential improvement is to have the settlement system support rollbacks.
 return False
```

### 2.3. `simulation.agents.government.Government` (Logic Change)

The `invest_infrastructure` method will be updated to use the new synchronous bond issuance.

**Pseudo-code:**
```python
def invest_infrastructure(self, current_tick: int, reflux_system: Any) -> bool:
 cost = self.config_module.INFRASTRUCTURE_INVESTMENT_COST

 # 1. Check if deficit financing is needed.
 if self.assets < cost:
 needed = cost - self.assets
 # 2. Call the new synchronous bond issuance method.
 financing_success = self.finance_system.issue_treasury_bonds_synchronous(
 issuer=self,
 amount_to_raise=needed,
 current_tick=current_tick
 )
 # 3. If financing fails, abort the investment.
 if not financing_success:
 logger.error(f"INFRASTRUCTURE_FAIL | Synchronous financing failed. Aborting investment.")
 return False

 # 4. At this point, funds are guaranteed to be in the account. Proceed with direct settlement.
 transfer_success = self.settlement_system.transfer(
 sender=self,
 recipient=reflux_system,
 amount=cost,
 description="Infrastructure Investment (Direct)"
 )

 if not transfer_success:
 # This indicates a severe issue, as funds should have been available.
 logger.critical(f"INFRASTRUCTURE_CATASTROPHE | Settlement failed even after successful financing!")
 return False

 self.expenditure_this_tick += cost
 self.infrastructure_level += 1
 logger.info("Infrastructure investment successful.")
 return True

```

### 2.4. `simulation.systems.ministry_of_education.MinistryOfEducation` (Logic Change)

The `run_public_education` method will adopt the same robust pattern, ensuring funds are secured *before* attempting to spend.

**Pseudo-code:**
```python
def run_public_education(self, households: List[Any], government: Any, ...):
 edu_budget = government.revenue_this_tick * self.config_module.PUBLIC_EDU_BUDGET_RATIO
 total_cost_of_education = self.calculate_total_potential_cost(households) # Calculate required funds upfront

 # 1. Check if deficit financing is needed.
 if government.assets < total_cost_of_education:
 needed = total_cost_of_education - government.assets
 financing_success = government.finance_system.issue_treasury_bonds_synchronous(
 issuer=government,
 amount_to_raise=needed,
 current_tick=current_tick
 )
 if not financing_success:
 logger.warning("Education spending aborted due to financing failure.")
 return # Abort

 # 2. Proceed with individual transfers, which are now safe.
 for agent in households:
 # ... existing logic to determine who gets education ...
 cost = ...
 if government.assets >= cost: # Re-check for safety in loop
 transfer_success = settlement_system.transfer(government, reflux_system, cost, "Education Grant")
 if transfer_success:
 agent.education_level += 1
 # ... update stats
 else:
 logger.critical("Education budget miscalculation!")
 break # Stop if funds run out unexpectedly
```

## 3. Validation Plan

To prove the fix, a focused integration test will be created in `tests/integration/test_fiscal_integrity.py`. This test will verify the atomicity of the deficit spending operation in isolation, avoiding false failures from the unrelated Tick 1 leak.

### Test Case: `test_infrastructure_investment_is_zero_sum`

1. **Setup**:
 * Instantiate a `Government` agent with `assets = 1000`.
 * Instantiate a `Bank` agent (the bond buyer) with `assets = 10000`.
 * Instantiate a `RefluxSystem` (the investment recipient) with `assets = 0`.
 * Instantiate a `SettlementSystem` and a `FinanceSystem`. Wire them together and to the agents.
 * Set `INFRASTRUCTURE_INVESTMENT_COST` to `5000`.

2. **Execution**:
 * Call `government.invest_infrastructure(current_tick=1, reflux_system=reflux_system)`.

3. **Assertions**:
 * The `Government` needs `4000`. The `FinanceSystem` should execute a synchronous transfer from the `Bank`.
 * **Bank Balance**: Assert `bank.assets == 10000 - 4000 = 6000`.
 * **Government Balance before spending**: Inside the mocked `finance_system`, we can assert `government.assets` becomes `1000 + 4000 = 5000`.
 * **Government Final Balance**: Assert `government.assets == 5000 - 5000 = 0`.
 * **Reflux System Balance**: Assert `reflux_system.assets == 5000`.
 * **Zero-Sum Check**: Assert the sum of final assets (`0 + 6000 + 5000`) equals the sum of initial assets (`1000 + 10000 + 0`). **Total change must be 0.**

A similar test, `test_education_spending_is_zero_sum`, will be created for the Ministry of Education logic.

## 4. Risk & Impact Analysis

This design directly addresses the risks identified in the pre-flight audit:

- **Zero-Sum Drift**: **Mitigated**. By exclusively using the `SettlementSystem` for direct transfers and completely avoiding the `TransactionProcessor`, we bypass the component identified as a potential source of "drift" and phantom fees.
- **Scheduler Dependency**: **Mitigated**. The fix does not require re-ordering the main simulation loop in `tick_scheduler.py`. It resolves the timing issue internally by making the financing operation synchronous, aligning it with the spending mechanism.
- **God Class Regression**: **Contained**. The changes are narrowly scoped to the bond issuance and infrastructure/education spending paths. The `Transaction`-based welfare and stimulus systems are unaffected, minimizing the risk of regression.
- **Validation Obscurity**: **Addressed**. The validation plan specifies a focused integration test that verifies the fiscal operation's zero-sum nature in isolation, ensuring the test is not contaminated by the unrelated global financial leak.

---

## 5. Jules Implementation Checklist

- [ ] Implement the new `issue_treasury_bonds_synchronous` method in `FinanceSystem` and its interface.
- [ ] Refactor `government.invest_infrastructure` to use the new synchronous financing mechanism.
- [ ] Refactor `ministry_of_education.run_public_education` to use the same robust, pre-financed pattern.
- [ ] Implement the integration tests defined in the Validation Plan.
- [ ] **Mandatory Reporting**: Document any observed difficulties or potential improvements regarding the `SettlementSystem` or agent interactions in a new file under `communications/insights/WO-117-Sync-Settlement-Feedback.md`.
```
