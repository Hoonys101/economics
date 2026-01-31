# Spec: [] Fractional Reserve Banking & Auditable Credit

## 1. Overview & Goals

This specification details the refactoring of the `Bank` module to implement a fractional reserve banking system that is fully compliant with the project's `ARCH_TRANSACTIONS.md` mandate. The primary goal is to eliminate direct state manipulation of the money supply and introduce an auditable, transaction-based mechanism for credit creation and destruction.

This change is critical to fixing the integrity checks in `scripts/trace_leak.py` and ensuring the simulation's economic stability.

- **Phase 1: Transactional Credit Creation**: Modify `Bank.grant_loan` to generate a `credit_creation` transaction instead of directly altering `Government` state.
- **Phase 2: Transactional Credit Destruction**: Modify `Bank.void_loan` and `Bank.process_default` to generate `credit_destruction` transactions.
- **Phase 3: Centralized Accounting**: Update the `Government` or a new `CentralBank` entity to process these transactions and accurately track the M2 money supply.
- **Phase 4: Verification**: Update `scripts/trace_leak.py` to correctly audit the system with the new accounting in place.

## 2. Interface & DTOs (No Changes)

The existing interfaces and DTOs within `modules/finance/api.py` are sufficient. This implementation will primarily use:
- `IBankService`
- `LoanInfoDTO`
- `BorrowerProfileDTO`
- `Transaction` (from `simulation.models`)

No new public-facing API changes are required. The refactoring is internal to the financial engine.

## 3. Detailed Logic & Pseudo-code

### 3.1. `simulation/bank.py`: `grant_loan` Refactoring

The `grant_loan` method will be modified to no longer communicate directly with the `Government`. Instead, it will book the internal loan/deposit and **generate a transaction** that serves as a notice of money creation for the central monetary authority.

```python
# In simulation/bank.py

# This method's signature does not change, but its return type will now be a tuple:
# Optional[Tuple[LoanInfoDTO, Transaction]]
def grant_loan(self, borrower_id: str, ...) -> Optional[Tuple[LoanInfoDTO, Transaction]]:
 """
 Grants a loan, creates a deposit, and generates a credit_creation transaction.
 """
 # ... (Steps 1: Credit Assessment - unchanged)

 # Step 2: Solvency Check (Reserve Requirement)
 gold_standard_mode = self._get_config("gold_standard_mode", False)
 if gold_standard_mode:
 if self.assets < amount:
 logger.warning("LOAN_DENIED | Gold Standard: Insufficient assets.")
 return None
 else:
 # Fractional Reserve Logic
 reserve_ratio = self._get_config("reserve_req_ratio", 0.1)
 # Total deposits include all existing deposits PLUS the new one to be created
 projected_total_deposits = sum(d.amount for d in self.deposits.values()) + amount
 required_reserves = projected_total_deposits * reserve_ratio

 if self.assets < required_reserves:
 logger.warning(f"LOAN_DENIED | Insufficient reserves. Assets: {self.assets:.2f} < Required: {required_reserves:.2f}")
 return None

 # Step 3: Credit Creation (Book Loan, Create Deposit, Generate TX)
 loan_id = f"loan_{self.next_loan_id}"
 self.next_loan_id += 1

 # ... (Term calculation logic - unchanged)

 # Create the new deposit locally (money creation on the bank's books)
 deposit_id = self.deposit_from_customer(int(borrower_id), amount)

 new_loan = Loan(
 # ... (Loan attribute setup - unchanged)
 created_deposit_id=deposit_id
 )
 self.loans[loan_id] = new_loan

 # --- CRITICAL CHANGE: Generate Transaction instead of direct modification ---
 # OLD: self.government.total_money_issued += amount

 # NEW: Create a transaction to notify the monetary authority
 credit_creation_tx = Transaction(
 buyer_id=self.id, # The bank is the "buyer" of this record
 seller_id=self.government.id, # The government is the symbolic recipient
 item_id=f"credit_creation_{loan_id}",
 quantity=1,
 price=amount, # The amount of money created
 market_id="monetary_policy",
 transaction_type="credit_creation",
 time=self.current_tick_tracker
 )

 loan_info_dto = LoanInfoDTO(
 # ... (DTO creation - unchanged)
 )

 # The orchestrator (e.g., TransactionManager) will now be responsible
 # for processing the returned transaction.
 return loan_info_dto, credit_creation_tx
```

### 3.2. `simulation/bank.py`: `void_loan` Refactoring

Symmetrically, `void_loan` must generate a `credit_destruction` transaction.

```python
# In simulation/bank.py

# This method will also return a transaction
def void_loan(self, loan_id: str) -> Optional[Transaction]:
 """
 Cancels a loan, reverses the deposit, and generates a credit_destruction transaction.
 """
 if loan_id not in self.loans:
 return None

 loan = self.loans[loan_id]
 amount = loan.principal

 # ... (Logic to reverse the deposit - unchanged)
 # This logic is critical and must succeed. If it fails, an error should be raised
 # and the destruction transaction should NOT be created.

 # 1. Reverse Deposit (Liability)
 # ...
 # 2. Destroy Loan (Asset)
 # ...

 # --- CRITICAL CHANGE: Generate Transaction instead of direct modification ---
 # OLD: self.government.total_money_issued -= amount

 # NEW: Create a transaction to notify the monetary authority
 credit_destruction_tx = Transaction(
 buyer_id=self.government.id, # Symbolic sender
 seller_id=self.id, # Symbolic receiver
 item_id=f"credit_destruction_{loan_id}",
 quantity=1,
 price=amount, # The amount of money destroyed
 market_id="monetary_policy",
 transaction_type="credit_destruction",
 time=self.current_tick_tracker
 )

 logger.info(f"LOAN_VOIDED | Loan {loan_id} cancelled. Destruction tx generated.")
 return credit_destruction_tx

```

### 3.3. Monetary Authority (Government) Accounting

The `Government` class must be updated to track the monetary delta based on the new transaction types.

```python
# In simulation/agents/government.py (or a dedicated CentralBank class)

class Government:
 def __init__(self, ...):
 # ...
 # This will track the net change in money supply from credit this tick
 self.credit_delta_this_tick = 0.0

 def reset_tick_trackers(self):
 # ... (other resets)
 self.credit_delta_this_tick = 0.0

 def process_monetary_transactions(self, transactions: List[Transaction]):
 """
 Processes transactions related to monetary policy.
 """
 for tx in transactions:
 if tx.transaction_type == "credit_creation":
 self.credit_delta_this_tick += tx.price
 # This attribute is now officially managed here
 self.total_money_issued += tx.price
 elif tx.transaction_type == "credit_destruction":
 self.credit_delta_this_tick -= tx.price
 # This attribute is now officially managed here
 self.total_money_destroyed += tx.price

 def get_monetary_delta(self) -> float:
 """
 Returns the net change in the money supply authorized this tick.
 """
 # This now includes both minting/burning and credit creation/destruction
 # Assuming `minted_this_tick` and `burned_this_tick` are handled elsewhere
 base_money_delta = self.minted_this_tick - self.burned_this_tick
 return base_money_delta + self.credit_delta_this_tick

```

## 4. Verification Plan

The `scripts/trace_leak.py` script must be adjusted to accommodate the new workflow where `grant_loan` returns a transaction that needs to be processed.

### `trace_leak.py` Algorithm Change

```python
# In scripts/trace_leak.py

def trace():
 print("--- TRACE START ---")
 sim = create_simulation()

 # Let's find a firm to grant a loan to
 target_firm = next((f for f in sim.world_state.firms if f.is_active), None)
 if not target_firm:
 print("No active firm found for loan test.")
 return

 # Grant a loan BEFORE the tick runs to see the effect
 loan_amount = 5000.0
 interest_rate = 0.05

 # The world state or a transaction manager must now handle the output of grant_loan
 loan_result = sim.bank.grant_loan(
 borrower_id=str(target_firm.id),
 amount=loan_amount,
 interest_rate=interest_rate,
 borrower_profile=target_firm.get_borrower_profile() # Assuming this method exists
 )

 # Process the resulting transaction
 if loan_result:
 _loan_info, credit_tx = loan_result
 # The government must process this to update its internal delta tracker
 sim.government.process_monetary_transactions([credit_tx])
 print(f"Loan granted to Firm {target_firm.id} for {loan_amount:,.2f}. Credit TX processed.")

 baseline_money = sim.world_state.calculate_total_money()
 print(f"Tick 0 (START) Total Money: {baseline_money:,.2f}")

 # Now run the tick, which will process other transactions
 sim.run_tick()

 current_money = sim.world_state.calculate_total_money()
 # The authorized delta is now correctly calculated by the government
 authorized_delta = sim.government.get_monetary_delta()
 actual_delta = current_money - baseline_money

 print(f"\nTick 1 (END) Total Money: {current_money:,.2f}")
 print(f"Baseline: {baseline_money:,.2f}")
 print(f"Authorized Delta (Minted - Destroyed + Credit): {authorized_delta:,.2f}")
 print(f"Actual Delta: {actual_delta:,.2f}")

 # Check Integrity
 leak = actual_delta - authorized_delta
 if abs(leak) > 1e-9: # Use a small epsilon for float comparison
 print(f"❌ LEAK DETECTED: {leak:,.4f}")
 sys.exit(1)
 else:
 print(f"✅ INTEGRITY CONFIRMED (Leak: {leak:,.4f})")

```

## 5. Risk & Impact Audit

This design directly addresses the risks identified in the pre-flight audit.

1. **Direct State Manipulation (Mitigated)**: The `Bank` no longer modifies `Government` state. It generates auditable `Transaction` objects, adhering to the `ARCH_TRANSACTIONS.md` protocol.
2. **Accounting Integrity Failure (Mitigated)**: The `Government.get_monetary_delta()` method now has full visibility into credit-based money supply changes, allowing `trace_leak.py` to function as intended.
3. **SRP Violation (Mitigated)**: The `Bank`'s responsibility is now correctly limited to commercial banking. The `Government` (acting as Central Bank) is solely responsible for system-wide monetary accounting.
4. **Incomplete Rollback Logic (Mitigated)**: The `void_loan` function now generates a symmetrical `credit_destruction` transaction, ensuring that credit lifecycle operations remain balanced and auditable.

## 6. Mocking & Golden Data

No changes to `conftest.py` fixtures or golden data are required. The primary validation for this architectural change is the successful execution of the updated `scripts/trace_leak.py` script, which serves as a live integration test of the financial engine's integrity.
