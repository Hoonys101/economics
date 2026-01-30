# Technical Specification: SPEC_MONEY_LEAK_FIX

- **ID**: SPEC_MONEY_LEAK_FIX
- **Title**: Elimination of Direct Asset Modification to Enforce Zero-Sum Integrity
- **Status**: Proposed
- **Author**: Scribe (Gemini)
- **Reviewer**: Antigravity (Team Leader)

---

## 1. Overview

### 1.1. Problem Statement
The simulation is experiencing critical "money leak" bugs, where the total money supply (M2) drifts uncontrollably, leading to economic instability and invalid results (e.g., GDP=0). The root cause has been identified as direct asset modifications (`_add_assets`, `_sub_assets`) within various system modules. These modifications bypass the centralized `SettlementSystem`, which is the sole authority for ledgering financial transactions and maintaining zero-sum integrity.

### 1.2. Proposed Solution
This specification mandates the complete refactoring of `housing_system.py`, `demographic_manager.py`, and `firm_management.py` to eliminate all direct calls to `_add_assets` and `_sub_assets`. All financial transfers, without exception, must be executed through `simulation.settlement_system.transfer()`. A missing or unavailable `SettlementSystem` will be treated as a fatal error, halting the simulation to prevent data corruption.

## 2. Core Mandate: Elimination of Direct Asset Modification

The use of `_add_assets` and `_sub_assets` within the modules listed below is strictly **FORBIDDEN**. These methods are to be considered protected and callable **only** by the `SettlementSystem` itself.

All financial state changes must be performed by invoking methods on the settlement system, primarily `transfer()`, accessed via the monolithic simulation object:
`simulation.settlement_system.transfer(debit_agent, credit_agent, amount, memo, tick=simulation.time)`

## 3. Module-Specific Refactoring Guides

### 3.1. `simulation/systems/firm_management.py`

#### 3.1.1. `spawn_firm`: Startup Capital Injection
- **Context**: The `spawn_firm` method transfers startup capital from a founder to a new firm. The current implementation contains a legacy fallback that uses direct asset modification.
- **Action**:
  1.  Remove the entire `else` block that contains the legacy `founder_household._sub_assets(...)` and `new_firm._add_assets(...)` calls.
  2.  The `settlement_system.transfer(...)` call is now the **only** mechanism for this transfer.
  3.  If the transfer fails (returns `False`), the function must abort the firm's creation and return `None`.

- **Pseudo-code (Before):**
  ```python
  if settlement_system:
      success = settlement_system.transfer(...)
  else:
      # LEGACY FALLBACK TO BE REMOVED
      founder_household._sub_assets(final_startup_cost)
      new_firm._add_assets(final_startup_cost)
      success = True
  ```

- **Pseudo-code (After):**
  ```python
  settlement_system = simulation.settlement_system
  if not settlement_system:
      raise RuntimeError("SettlementSystem not available. Cannot complete financial transactions.")

  success = settlement_system.transfer(
      founder_household, new_firm, final_startup_cost, f"Startup Capital for Firm {new_firm.id}"
  )

  if not success:
      logger.warning(...)
      return None # Abort firm creation
  ```

### 3.2. `simulation/systems/housing_system.py`

#### 3.2.1. `process_housing`: Rent Collection
- **Context**: A tenant pays rent to an owner.
- **Action**: Replace the two separate `_sub_assets` and `_add_assets` calls with a single `transfer` call.

- **Pseudo-code (Before):**
  ```python
  if tenant.assets >= rent:
      tenant._sub_assets(rent)
      owner._add_assets(rent)
  else:
      # Eviction
  ```

- **Pseudo-code (After):**
  ```python
  success = simulation.settlement_system.transfer(tenant, owner, rent, "rent_payment")
  if not success:
      # Eviction due to insufficient funds
      logger.info(f"EVICTION | Household {tenant.id} ... insufficient funds for rent.")
      # ... eviction logic ...
  ```

#### 3.2.2. `process_housing`: Maintenance Cost
- **Context**: An owner pays maintenance costs to the government. The current code has a fallback.
- **Action**: Remove the fallback `owner._sub_assets(payable)` logic. Enforce the use of `settlement_system.transfer`.

- **Pseudo-code (After):**
  ```python
  # (Inside loop)
  cost = unit.estimated_value * self.config.MAINTENANCE_RATE_PER_TICK
  if cost > 0:
      simulation.settlement_system.transfer(
          owner,
          simulation.government,
          cost, # The transfer method will handle insufficient funds
          "housing_maintenance",
          tick=simulation.time
      )
  ```

#### 3.2.3. `process_transaction`: Housing Purchase
- **Context**: A complex, multi-step transaction involving a buyer, seller, and potentially a bank loan.
- **Action**: Decompose the transaction into a strict sequence of `SettlementSystem` calls and bank interactions.
  1.  **Loan Funds**: The `buyer._add_assets(loan_amount)` call is illegal. The bank's `withdraw_for_customer` method, which correctly modifies the agent's cash balance and the bank's reserves, is the correct approach and must be used. The fallback path must be removed.
  2.  **Payment Transfer**: The separate `buyer._sub_assets(trade_value)` and `seller._add_assets(trade_value)` calls must be replaced with a single `simulation.settlement_system.transfer()` call.
  3.  **Government Seller**: The existing logic that uses `seller.collect_tax()` for government sales is acceptable, as this method is expected to use the `SettlementSystem` internally. This pattern should be preserved.

- **Pseudo-code (After `process_transaction`):**
  ```python
  # ...
  # 1. Mortgage Logic (remains mostly the same)
  if loan_info:
      # ...
      # The bank's internal logic creates the deposit.
      # The withdrawal makes it available as cash to the agent.
      success = simulation.bank.withdraw_for_customer(buyer.id, loan_amount)
      if not success:
          # Loan withdrawal failed, rollback and abort transaction.
          simulation.bank.void_loan(loan_id)
          return
      # NO direct asset modification for buyer
  # ...

  # 2. Process Funds Transfer
  # The buyer now has the loan cash + their original assets.
  success = simulation.settlement_system.transfer(
      buyer, seller, trade_value, f"purchase_unit_{unit.id}"
  )
  if not success:
      # This should not happen if buyer assets were sufficient.
      # But if it does, we must rollback the loan.
      logger.error("FATAL: Failed to transfer funds for housing purchase after loan was secured.")
      if loan_info:
          simulation.bank.void_loan(loan_info["loan_id"])
      return # Abort transaction

  # 3. Transfer Title and update agent properties (no financial changes here)
  # ...
  ```

### 3.3. `simulation/systems/demographic_manager.py`

#### 3.3.1. `process_births`: Birth Gift
- **Context**: A parent gives a financial gift to a newborn child.
- **Action**: The current implementation `WO-124` correctly uses `settlement.transfer()`. The specification confirms this is the mandatory pattern. The fallback error logging is also correct. No changes are needed other than ensuring no legacy code remains.

#### 3.3.2. `handle_inheritance`: Estate Distribution
- **Context**: A deceased agent's assets are distributed to the government (tax) and heirs. The current logic uses direct asset modification.
- **Action**: Replace the entire financial distribution block with a series of `transfer` calls. The final call to `deceased_agent._sub_assets` must be removed as it is now redundant.

- **Pseudo-code (Before):**
  ```python
  # ...
  simulation.government.collect_tax(...) # This is OK
  share = net_amount / len(heirs)
  for heir in heirs:
      heir._add_assets(share) # FORBIDDEN
  deceased_agent._sub_assets(deceased_agent.assets) # FORBIDDEN
  ```

- **Pseudo-code (After):**
  ```python
  amount = deceased_agent.assets
  if amount <= 0: return

  tax_rate = self.config_module.INHERITANCE_TAX_RATE
  tax_amount = amount * tax_rate
  net_estate = amount - tax_amount

  # 1. Transfer tax to government
  if tax_amount > 0:
      simulation.settlement_system.transfer(
          deceased_agent, simulation.government, tax_amount, "inheritance_tax"
      )

  # 2. Distribute remainder to heirs
  if net_estate > 0 and heirs:
      share = net_estate / len(heirs)
      for heir in heirs:
          simulation.settlement_system.transfer(
              deceased_agent, heir, share, "inheritance_distribution"
          )

  # The deceased agent's assets are now correctly debited to near-zero by the transfers.
  # No final _sub_assets call is needed or allowed.
  ```

## 4. Architectural & Testing Impact

### 4.1. System Access and Error Handling
Access to the settlement system **MUST** be through `simulation.settlement_system`. Any module that performs a financial transaction must assume this object is non-nullable.

**Mandate**: A check for the settlement system's existence must be performed. If it is `None`, a `RuntimeError` must be raised to halt the simulation. Graceful degradation or fallbacks that bypass the ledger are strictly forbidden.

```python
# At the beginning of any financially-sensitive method:
settlement_system = simulation.settlement_system
if not settlement_system:
    raise RuntimeError(f"CRITICAL: SettlementSystem not found in {self.__class__.__name__}. Halting to prevent data corruption.")
```

### 4.2. Test Suite Migration Strategy
This refactoring will cause widespread test failures. The following migration plan must be executed.

1.  **Identify Affected Tests**: All test files corresponding to `housing_system`, `demographic_manager`, and `firm_management` are affected.
2.  **Mock `SettlementSystem`**: Mocks of the `simulation` object used in tests **MUST** be updated to include a mock of `settlement_system`.
    -   Example: `mock_simulation.settlement_system = mock_settlement_system`
    -   The `mock_settlement_system.transfer` method should be configured to return `True` by default for successful transaction tests, and `False` for failure-case tests.
3.  **Refactor Test Setups**: Any test setup code that uses `_add_assets` or `_sub_assets` to prepare agent states must be refactored.
    -   To grant an agent initial assets for a test, use a mocked `settlement_system.create_and_transfer`.
    -   Alternatively, for transfers between test agents, use `settlement_system.transfer`.
4.  **Refactor Assertions**: Assertions against `agent.assets` are still valid. However, the "Act" phase of the test must now trigger a call to the system under test, which in turn calls the mocked `settlement_system.transfer`, rather than directly modifying assets.

## 5. Verification Plan

1.  **Static Analysis**: After refactoring, run a project-wide search (`grep` or equivalent) for the strings `_add_assets` and `_sub_assets` within the three target `.py` files. The search must return zero matches.
2.  **Unit & Integration Tests**: The entire test suite must pass after the test migration is complete.
3.  **Zero-Sum Verification**: A long-running simulation scenario, previously identified as a source of M2 drift, will be executed.
    -   **Metric**: Log the total money supply at every tick (`sum(agent.assets for agent in all_agents) + bank_reserves`).
    -   **Success Criteria**: The total money supply must remain constant, except for explicit and logged money creation/destruction events initiated by the `CentralBank` (e.g., `create_and_transfer`) or `Government` (e.g., `transfer_and_destroy`). Any unlogged change indicates a remaining leak.
