# Spec: TD-105 Atomic Investment Transfer

## 1. Objective
To eliminate the positive money drift (TD-105) by enforcing atomic, conditional transfers for all investment expenditures that target the `EconomicRefluxSystem`. This ensures that money is only credited to the reflux system if it has been verifiably debited from the investing agent, maintaining the zero-sum principle for these internal economic flows.

## 2. Problem Analysis
The root cause of the money creation is the use of a non-atomic `SettlementSystem.transfer()` method for investment activities in `simulation/agents/government.py` and `simulation/components/finance_department.py`. This method credits the `EconomicRefluxSystem` but does not guarantee a corresponding, successful debit from the sender's assets.

Code forensics (`TD105_DRIFT_FORENSICS.md`) and comments (`government.py:L575`) indicate this bypass of the standard `TransactionProcessor` was an intentional, albeit flawed, attempt to avoid a separate issue described as "zero-sum drift" or "phantom tax/leaks."

Therefore, the solution must not simply revert to using the `TransactionProcessor`. Instead, it must fix the designated `SettlementSystem.transfer` method to make it safe and atomic.

## 3. Proposed Solution: Atomic Settlement Transfer

### 3.1. Modify `ISettlementSystem` and its Implementation
The core of the fix is to redefine `ISettlementSystem.transfer()` to be an atomic and conditional operation.

#### 3.1.1. `modules/finance/api.py` (Interface Definition)
The interface for `transfer` in `ISettlementSystem` should be updated to reflect its fallibility.

```python
# In modules/finance/api.py, within ISettlementSystem class

class ISettlementSystem(ABC):
    # ... other methods
    @abstractmethod
    def transfer(
        self,
        debit_agent: "IFinancialEntity",
        credit_agent: "IFinancialEntity",
        amount: float,
        memo: str
    ) -> bool:
        """
        Atomically transfers an amount from one financial entity to another.

        This operation MUST be atomic. It checks if the debit_agent has
        sufficient funds. If so, it debits the debit_agent and credits the
        credit_agent. If not, the operation fails and no state is changed.

        Args:
            debit_agent: The entity from which to withdraw funds.
            credit_agent: The entity to which to deposit funds.
            amount: The amount to transfer.
            memo: A description of the transaction.

        Returns:
            True if the transfer was successful, False otherwise.
        """
        ...
```

#### 3.1.2. `simulation/finance/settlement_system.py` (Concrete Implementation)
The concrete implementation of `transfer` must be modified to follow this logic:

```python
# Pseudo-code for the implementation of SettlementSystem.transfer

def transfer(self, debit_agent, credit_agent, amount, memo) -> bool:
    if amount <= 0:
        logger.warning(f"Transfer of non-positive amount ({amount}) attempted. Memo: {memo}")
        return True # Or False, based on desired strictness. Let's say True.

    # 1. ATOMIC CHECK: Verify funds BEFORE any modification
    if debit_agent.assets < amount:
        logger.error(
            f"SETTLEMENT_FAIL | Insufficient funds for {debit_agent.id} to transfer {amount:.2f} to {credit_agent.id}. "
            f"Assets: {debit_agent.assets:.2f}. Memo: {memo}",
            extra={"tags": ["settlement", "insufficient_funds"]}
        )
        return False

    # 2. EXECUTE: Perform the debit and credit
    try:
        # These should be calls to the IFinancialEntity interface methods
        debit_agent.withdraw(amount)
        credit_agent.deposit(amount)

        logger.debug(
            f"SETTLEMENT_SUCCESS | Transferred {amount:.2f} from {debit_agent.id} to {credit_agent.id}. Memo: {memo}",
            extra={"tags": ["settlement"]}
        )
        return True

    except InsufficientFundsError as e:
        # This is a fallback/safety check in case of race conditions or flawed asset properties.
        # The initial check should prevent this. No need to rollback as no state was changed yet.
        logger.critical(
            f"SETTLEMENT_CRITICAL | Race condition or logic error. InsufficientFundsError during transfer. "
            f"Initial check passed but withdrawal failed. Details: {e}",
            extra={"tags": ["settlement", "error"]}
        )
        # We must ensure credit_agent was not credited. If withdraw() happens before deposit(), this is safe.
        return False
    except Exception as e:
        # Handle other potential errors, but the key is to ensure no partial transaction.
        logger.exception(
             f"SETTLEMENT_UNHANDLED_FAIL | An unexpected error occurred during transfer. Details: {e}"
        )
        # CRITICAL: If debit_agent.withdraw() succeeded but credit_agent.deposit() failed,
        # we have now destroyed money. The implementation must be robust.
        # The simplest robust implementation is withdraw then deposit. If deposit fails, we must revert the withdraw.
        # However, for this spec, we assume withdraw() and deposit() are simple property changes and cannot fail
        # if the initial checks pass.
        return False

```

### 3.2. Update Call Sites to Handle Transfer Failures
The methods initiating these investments must now check the return value of `transfer()` and abort the investment if it fails.

#### 3.2.1. `simulation/agents/government.py`

```python
# In simulation/agents/government.py, inside invest_infrastructure method

# ... (code to calculate cost and handle financing) ...

# This line is the critical change
transfer_success = self.settlement_system.transfer(
     self,
     reflux_system,
     effective_cost,
     "Infrastructure Investment (Direct)"
)

# NEW: Handle failure
if not transfer_success:
     logger.error(f"INFRASTRUCTURE_FAIL | Settlement transfer of {effective_cost:.2f} failed. Aborting investment.")
     return False, transactions # Return failure and any financing txs

# This code only runs on successful transfer
self.expenditure_this_tick += effective_cost
self.infrastructure_level += 1
# ... (logging)
return True, transactions
```

#### 3.2.2. `simulation/components/finance_department.py`
The investment methods (`invest_in_automation`, `invest_in_rd`, `invest_in_capex`) must be updated.

```python
# In simulation/components/finance_department.py, example for invest_in_rd

def invest_in_rd(self, amount: float, reflux_system: Optional[Any] = None) -> bool:
    # The initial cash check is now redundant but acts as a good pre-check
    if self._cash < amount:
        return False

    if hasattr(self.firm, 'settlement_system') and self.firm.settlement_system and reflux_system:
        # CRITICAL CHANGE: Check the return value
        transfer_success = self.firm.settlement_system.transfer(self.firm, reflux_system, amount, "R&D Investment")

        if transfer_success:
            # This expense should only be recorded on successful transfer
            self.record_expense(amount)
            return True
        else:
            # NEW: Log failure and do not record expense
            self.firm.logger.warning(f"R&D investment of {amount:.2f} failed due to failed settlement transfer.")
            return False
    else:
        self.firm.logger.warning("INVESTMENT_BLOCKED | Missing SettlementSystem or RefluxSystem for R&D.")
        return False

```
**The same pattern must be applied to `invest_in_automation` and `invest_in_capex`.**

## 4. Risk & Impact Audit
This fix addresses the risks identified in the pre-flight audit.
- **`SettlementSystem` Opacity**: The spec provides a clear, mandatory behavioral contract for `SettlementSystem.transfer`, mitigating the risk of its unseen implementation.
- **Intentional Bypass**: By making the bypass mechanism itself atomic and safe, we respect the original design decision to avoid the `TransactionProcessor` while fixing the bug it created.
- **`RefluxSystem.distribute`**: This fix correctly focuses on the `RefluxSystem`'s input. The `distribute` method, while architecturally questionable, now operates on a verifiably zero-sum balance, neutralizing its "money creation" side effect.
- **Economic Balance & Test Impact**: This fix **will** alter the simulation's macroeconomic outputs. The total money supply will be lower and more stable. Existing tests that rely on the inflated economy are expected to fail and **must be updated or replaced**. The primary success metric is the elimination of the money drift, not backward compatibility with a bugged economy.

## 5. Verification Plan

### 5.1. Unit Tests for `SettlementSystem`
- A test case where `debit_agent.assets` is less than `amount`. Assert that `transfer()` returns `False` and both agents' balances are unchanged.
- A test case where `debit_agent.assets` is greater than `amount`. Assert that `transfer()` returns `True`, `debit_agent.assets` has decreased by `amount`, and `credit_agent.assets` has increased by `amount`.

### 5.2. Integration Test Script (`scripts/verify_investment_atomicity.py`)
A new script should be created to perform an end-to-end test:
1.  Initialize a simulation.
2.  Select a `Firm` agent.
3.  **Scenario 1 (Failure):**
    -   Artificially set the firm's assets to `X`.
    -   Record the `EconomicRefluxSystem`'s balance (`B1`).
    -   Record the simulation's total money supply (`M1`).
    -   Call `firm.finance.invest_in_rd(X + 100, reflux_system)`.
    -   Assert the method returned `False`.
    -   Assert the `EconomicRefluxSystem`'s balance is still `B1`.
    -   Assert the total money supply is still `M1`.
4.  **Scenario 2 (Success):**
    -   Artificially set the firm's assets to `Y`.
    -   Record the `EconomicRefluxSystem`'s balance (`B2`).
    -   Record the simulation's total money supply (`M2`).
    -   Call `firm.finance.invest_in_rd(Y - 10, reflux_system)`.
    -   Assert the method returned `True`.
    -   Assert the `EconomicRefluxSystem`'s balance is now `B2 + (Y - 10)`.
    -   Assert the simulation's total money supply is still `M2` (or within a very small tolerance for floating point math).

### 5.3. Full Simulation Run
- Run a standard simulation for 1000+ ticks.
- Monitor the total money supply. It should now be stable, with predictable changes only from explicit central bank actions (credit creation, bond issuance) or loan defaults, not from firm/government investments.

## 6. Implementation Notes for Jules
- The most critical part of this task is ensuring the call sites (`government.py`, `finance_department.py`) correctly check the `bool` return value from the modified `settlement_system.transfer` and prevent the investment logic (e.g., `infrastructure_level += 1`, `record_expense`) from executing on failure.
- Ensure all three investment methods in `FinanceDepartment` are updated, not just one.
- The `IFinancialEntity` interface methods `withdraw(amount)` and `deposit(amount)` are the correct, low-level methods to use inside the `SettlementSystem`. Avoid direct `_assets` manipulation.
