# Phase B: Tick Sequence Normalization Spec

## 1. Objective
To achieve 100% transactional integrity within the simulation by refactoring all asset transfers to occur within a single, unified, and atomic transaction phase (`_phase_transactions`). This involves converting all direct state-modifying calls (`settlement_system.transfer`, `withdraw`, `deposit`) into pure functions that generate and return a `List[Transaction]`, which are then executed by the `TransactionProcessor`.

This specification is based on the findings in `design/audits/AUDIT_WO116_PHASE_B_READINESS.md`.

## 2. Core Architectural Change: Production Re-sequencing (Track B)

To resolve the circular dependency of corporate tax calculation, the firm production loop must be moved to execute *before* the Sacred Sequence.

**⚠️ CRITICAL IMPACT**: This is a fundamental change to the economic model. Firms will now base their current-tick decisions (hiring, pricing) on the production and profit outcomes calculated from the *previous* tick's state. All existing AI models and agent heuristics will be impacted and require re-evaluation.

### 2.1. `simulation/tick_scheduler.py` Modification

The following block of code must be moved:

**FROM (Current Position):** `simulation/tick_scheduler.py` (after the Sacred Sequence, approx. line 369)
```python
 # ---------------------------------------------------------
 # Activate Farm Logic (Production & Needs/Wages)
 # ---------------------------------------------------------
 for firm in state.firms:
 if firm.is_active:
 firm.produce(state.time, technology_manager=state.technology_manager)
 firm.update_needs(state.time, state.government, market_data, state.reflux_system)

 # 2a. Corporate Tax
 if firm.is_active and firm.current_profit > 0:
 tax_amount = state.government.calculate_corporate_tax(firm.current_profit)
 if state.settlement_system:
 state.settlement_system.transfer(firm, state.government, tax_amount, "corporate_tax")
 else:
 # Fallback
 firm._sub_assets(tax_amount)
 state.government._add_assets(tax_amount)
 state.government.collect_tax(tax_amount, "corporate_tax", firm.id, state.time)
```

**TO (New Position):** `simulation/tick_scheduler.py` (before the Sacred Sequence, immediately before the `_phase_decisions` call, approx. line 273)
```python
 # [NEW POSITION] FIRM PRODUCTION & PROFIT CALCULATION (PRE-DECISION)
 for firm in state.firms:
 if firm.is_active:
 firm.produce(state.time, technology_manager=state.technology_manager)
 # update_needs is now deferred to a transaction-generating function
 # Corporate Tax is now deferred to a transaction-generating function

 # ==================================================================================
 # THE SACRED SEQUENCE ()
 # ==================================================================================
```
**Note:** The `update_needs` and `Corporate Tax` logic will be removed from this loop and handled as part of the transaction generation in Track A.

## 3. Implementation Plan: Transaction Generation (Track A)

### 3.1. `simulation/tick_scheduler.py` Modifications

A new list will be created to aggregate all system-level transactions.

```python
# In TickScheduler.run_tick, before the Sacred Sequence (after the moved production loop)

# ... (existing code) ...

# [NEW] List to collect all non-market transactions
system_transactions: List[Transaction] = []

# --- [REFACTOR] Bank Interest Processing ---
# The bank.run_tick method will now return a list of transactions.
if hasattr(state.bank, "run_tick"):
 transactions_from_bank = state.bank.run_tick(state.agents, state.time, reflux_system=state.reflux_system)
 system_transactions.extend(transactions_from_bank)

# --- [REFACTOR] Firm Profit Distribution ---
for firm in state.firms:
 transactions_from_profit = firm.distribute_profit(state.agents, state.time)
 system_transactions.extend(transactions_from_profit)

# --- [REFACTOR] Service National Debt ---
transactions_from_debt = state.finance_system.service_debt(state.time)
system_transactions.extend(transactions_from_debt)

# --- [REFACTOR] Welfare and Wealth Tax ---
transactions_from_welfare = state.government.run_welfare_check(list(state.agents.values()), market_data, state.time)
system_transactions.extend(transactions_from_welfare)

# --- [REFACTOR] Corporate Tax Collection (UNBLOCKED) ---
# This logic is now unblocked by the production loop move.
for firm in state.firms:
 if firm.is_active and firm.current_profit > 0:
 tax_amount = state.government.calculate_corporate_tax(firm.current_profit)
 # Create transaction instead of direct transfer
 tax_transaction = Transaction(
 market_id="system",
 order_type="tax",
 item_id="corporate_tax",
 quantity=1,
 price=tax_amount,
 seller_id=firm.id,
 buyer_id=state.government.id,
 timestamp=state.time
 )
 system_transactions.append(tax_transaction)
 state.government.collect_tax(tax_amount, "corporate_tax", firm.id, state.time) # For tracking only

# ... (Other movable items like public education, M&A etc. follow the same pattern) ...

# ==================================================================================
# THE SACRED SEQUENCE ()
# ==================================================================================

# ... (inside _phase_matching)
# state.transactions will contain market transactions

def _phase_transactions(self, state: SimulationState) -> None:
 """Phase 3: Execute transactions."""
 # [NEW] Extend the market transactions with all collected system transactions
 state.transactions.extend(system_transactions) # system_transactions must be passed or accessible

 if self.world_state.transaction_processor:
 self.world_state.transaction_processor.execute(state)
 else:
 state.logger.error("TransactionProcessor not initialized.")
```
*Modify `_phase_transactions` to accept the `system_transactions` list or make it an attribute of the `TickScheduler` instance that is accessible within the method.*

### 3.2. Module Refactoring: Example `bank.py`

All identified "Movable" transfers must be refactored. The following example for `bank.run_tick` serves as the blueprint for all others.

**File:** `simulation/bank.py`
**Method:** `run_tick`

**Current Logic:**
```python
# ... inside run_tick loop ...
if agent.assets >= payment:
 if self.settlement_system:
 self.settlement_system.transfer(agent, self, payment, f"Loan Interest {loan_id}")
# ...
if self.assets >= interest_payout:
 if self.settlement_system:
 self.settlement_system.transfer(self, agent, interest_payout, f"Deposit Interest {dep_id}")
# ...
if net_profit > 0 and reflux_system:
 self._assets -= net_profit
 reflux_system.capture(net_profit, "Bank", "net_profit")
```

**New Logic:**
```python
# Change method signature
def run_tick(self, agents_dict: Dict[int, Any], current_tick: int = 0, reflux_system: Optional[Any] = None) -> List[Transaction]:

 generated_transactions: List[Transaction] = []
 # ...
 # 1. Collect Interest from Loans
 # ...
 # ... inside loop ...
 if agent.assets >= payment:
 # Create transaction instead of transferring
 loan_interest_tx = Transaction(
 market_id="system", order_type="loan_interest", item_id=loan_id,
 quantity=1, price=payment, seller_id=agent.id, buyer_id=self.id, timestamp=current_tick
 )
 generated_transactions.append(loan_interest_tx)
 total_loan_interest += payment
 # ...

 # 2. Pay Interest to Depositors
 # ... inside loop ...
 if self.assets >= interest_payout: # NOTE: This check is now optimistic. Solvency is handled by TransactionProcessor.
 deposit_interest_tx = Transaction(
 market_id="system", order_type="deposit_interest", item_id=dep_id,
 quantity=1, price=interest_payout, seller_id=self.id, buyer_id=agent.id, timestamp=current_tick
 )
 generated_transactions.append(deposit_interest_tx)
 total_deposit_interest += interest_payout
 # ...

 # 3. Bank Profit to Reflux System
 net_profit = total_loan_interest - total_deposit_interest
 if net_profit > 0 and reflux_system:
 # Transaction from Bank to a virtual Reflux entity, or handled differently.
 # For now, let's assume Reflux is not a standard entity. The transfer to reflux is a "leak" from the zero-sum system.
 # This spec will treat it as such. We will create a transaction to a conceptual GOV/REFLUX entity.
 reflux_tx = Transaction(
 market_id="system", order_type="reflux", item_id="bank_profit",
 quantity=1, price=net_profit, seller_id=self.id, buyer_id=reflux_system.id, # Assumes reflux has an ID
 timestamp=current_tick
 )
 # Note: TransactionProcessor must know how to handle reflux_system.id. A simpler way is to transfer to government,
 # which then funds the reflux system. Let's use government.
 reflux_tx_to_gov = Transaction(
 market_id="system", order_type="reflux_capture", item_id="bank_profit",
 quantity=1, price=net_profit, seller_id=self.id, buyer_id=self.government.id, # Assuming bank has gov reference
 timestamp=current_tick
 )
 generated_transactions.append(reflux_tx_to_gov)

 # ...
 return generated_transactions
```
**Apply this pattern to all "Movable" items listed in the audit.**

### 3.3. Module Refactoring: `modules/finance/system.py`

**Method:** `service_debt`

**New Logic:**
```python
# Change method signature
def service_debt(self, current_tick: int) -> List[Transaction]:
 generated_transactions: List[Transaction] = []
 matured_bonds = [b for b in self.outstanding_bonds if b.maturity_date <= current_tick]
 # ...
 for bond in matured_bonds:
 # ... calculate total_repayment ...
 bond_holder = self.bank # or self.central_bank

 repayment_tx = Transaction(
 market_id="system", order_type="bond_repayment", item_id=bond.id,
 quantity=1, price=total_repayment, seller_id=self.government.id, buyer_id=bond_holder.id,
 timestamp=current_tick
 )
 generated_transactions.append(repayment_tx)
 # Remove bond from internal list post-facto
 self.outstanding_bonds.remove(bond)

 return generated_transactions
```

## 4. Transaction Processor Contract
The existing `TransactionProcessor` is expected to handle the increased volume and variety of transactions in `state.transactions`. No modifications to the `TransactionProcessor` are required, as it is designed to iterate over a list of `Transaction` objects and call the `settlement_system` for each one. Its responsibility remains unchanged.

## 5. Verification Plan

### 5.1. Zero-Sum Integrity Check
Success is defined by the `MONEY_SUPPLY_CHECK` at the end of each tick in `tick_scheduler.py` consistently reporting a `delta` of `0.0` (or within a float precision tolerance of `1e-9`). Any non-zero delta indicates a leak or creation of money outside the sanctioned `CentralBank` mechanism and constitutes a failure of this work order.

### 5.2. Unit Test Refactoring
All unit tests that assert an agent's `assets` or other financial state immediately after calling a refactored function (e.g., `bank.run_tick`) **will fail and must be rewritten**.

- **Old Pattern (State Verification):**
 ```python
 initial_assets = agent.assets
 bank.run_tick(...)
 assert agent.assets == initial_assets + interest
 ```
- **New Pattern (Behavior Verification):**
 ```python
 transactions = bank.run_tick(...)
 assert len(transactions) == 1
 tx = transactions[0]
 assert tx.seller_id == bank.id
 assert tx.buyer_id == agent.id
 assert tx.price == expected_interest
 ```

### 5.3. New Integration Test
A new integration test, `tests/integration/test_tick_normalization.py`, must be created. This test will:
1. Set up a minimal world state with a few households, firms, and a government.
2. Capture the `baseline_money_supply` at the start.
3. Execute a single, full `TickScheduler.run_tick()`.
4. After the tick, re-calculate the `current_money` supply.
5. Assert that `current_money == baseline_money_supply`.

## 6. Risk & Impact Audit (Confirmation)
This specification directly addresses the risks identified in the pre-flight audit:
- **Temporal Dependency**: The spec mandates the re-sequencing of the production loop and explicitly warns of the economic model change.
- **SRP Violation / Signature Changes**: The spec provides a clear blueprint for changing function signatures to return `List[Transaction]`, centralizing execution responsibility.
- **Hidden Dependencies**: Acknowledged. The refactoring simplifies execution but not calculation logic. This remains as documented technical debt.
- **Test Invalidation**: The verification plan explicitly defines the required shift from state-based to behavior-based unit testing.

---

## 🚨 Mandatory Reporting
**Jules's Implementation Log:** During implementation, you are required to log any unforeseen complexities, deviations from this spec, or new insights. Save these findings in a new markdown file in `communications/insights/WO-116-Normalization-Log.md`. Any new architectural weaknesses discovered must be recorded in `design/TECH_DEBT_LEDGER.md`.
