File: communications\insights\phase23-spec-penny-perfect.md
```markdown
# Insight Report: Phase 23 - Operation Penny Perfect

## 1. Architectural Insights & Debt Analysis

### 1.1. The "Hasattr" Virus (Protocol Violation)
The audit of `SettlementSystem` revealed a critical violation of the "Protocol Purity" standard. The use of `hasattr(agent, 'id')` in `_get_engine` creates a "loose typing" loophole that allows non-compliant objects to pass as agents during tests. This undermines the `IAgent` protocol and masks contract failures.
- **Decision**: strict `isinstance(agent, IAgent)` checks will be enforced. The `_get_engine` method will raise `TypeError` if a participant does not satisfy the protocol, forcing tests to use proper Mocks.

### 1.2. Missing Monetary Levers
The `MonetaryTransactionHandler` logic was incomplete, missing explicit handling for `bailout` (Fiscal Injection) and `bond_issuance` (Debt Creation). Using `lender_of_last_resort` as a catch-all is semantically incorrect and complicates M2 tracking.
- **Decision**: These will be implemented as distinct branches in the `MonetaryTransactionHandler` to ensure correct logging and side-effect management (e.g., `bond_issuance` triggers `NationalDebt` updates).

### 1.3. Float Contamination Risk
While `SettlementSystem` enforces `int` at the boundary, there is a risk that `TransactionEngine` (which it delegates to) might still perform internal float math if not strictly typed.
- **Decision**: The Spec requires a "Pre-Flight Cast" to `int` for all amounts before they are passed to the `TransactionEngine` DTOs, ensuring the engine never sees a float.

## 2. Test Evidence Plan
(To be populated after implementation)
- `pytest tests/systems/test_settlement_system.py::test_strict_integer_pennies`
- `pytest tests/systems/test_monetary_handler.py::test_bailout_injection`
- `pytest tests/systems/test_bank_handler.py::test_protocol_adherence`

```

File: design\3_work_artifacts\specs\phase23_penny_perfect_spec.md
```markdown
# Spec: Phase 23 - Operation Penny Perfect

## 1. Overview
**Mission**: Enforce the "Penny Standard" (Integer Arithmetic) across the financial core and eliminate "loose typing" (`hasattr`) to restore architectural integrity.
**Owner**: Gemini-CLI
**Related Debts**: `TD-CRIT-FLOAT-CORE`, `TD-PROTO-MONETARY`, `TD-RUNTIME-TX-HANDLER`

---

## 2. Architectural Changes

### 2.1. SettlementSystem Hardening (`simulation/systems/settlement_system.py`)
**Objective**: Remove `hasattr` and enforce `IAgent` protocol.

- **Modification**: `_get_engine`
    - **Remove**: `if isinstance(agent, IAgent) or hasattr(agent, 'id'):`
    - **Add**: Strict `isinstance(agent, IAgent)` check.
    - **Error Handling**: Raise `TypeError(f"Agent {agent} does not implement IAgent protocol")` if check fails.
- **Modification**: `transfer` & `settle_atomic`
    - **Validation**: Ensure `amount` is explicitly cast to `int` before creating `TransactionDTO`.
    - **Guard**: `if not isinstance(amount, int): raise TypeError(...)` (Reinforce existing check).

### 2.2. Monetary Handler Expansion (`simulation/systems/handlers/monetary_handler.py`)
**Objective**: Register missing handlers and strictly type the logic.

- **New Support**:
    - `bailout`: Transfer from Central Bank (Mint) -> Agent (Target).
        - **Logic**: Similar to `lender_of_last_resort` but distinct log tag `BAILOUT_INJECTION`.
    - `bond_issuance`: Transfer from Agent (Buyer) -> Government (Seller).
        - **Logic**: Money moves to Government (Revenue) or Central Bank (Burn/Escrow).
        - **Assumption**: Bonds are sold by Government.

### 2.3. Bank Transaction Handler Implementation (`simulation/systems/handlers/bank_handler.py`)
**Objective**: Create a strict handler for `bank_deposit`, `bank_withdrawal`, `loan_repayment`.

- **Class**: `BankTransactionHandler(ITransactionHandler)`
- **Logic**:
    - **Deposit**: Cash (Wallet) -> Bank (Reserves). Update `BankAccount` ledger.
    - **Withdrawal**: Bank (Reserves) -> Cash (Wallet). Check Bank Liquidity.
    - **Loan Repayment**: Agent (Wallet) -> Bank (Capital/Revenue).
- **Constraints**:
    - MUST utilize `IBank` and `IFinancialEntity` protocols.
    - NO `hasattr` checks.

---

## 3. Pseudo-Code Implementation

### 3.1. MonetaryTransactionHandler (Update)

```python
class MonetaryTransactionHandler(ITransactionHandler):
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # Strict Protocol Check
        if not isinstance(context.settlement_system, IMonetaryAuthority):
             context.logger.error("Settlement System does not implement IMonetaryAuthority")
             return False

        if tx.transaction_type == "bailout":
            # Minting: CB -> Agent
            # Note: Buyer is usually CB, Seller is Agent (Recipient)
            return context.settlement_system.mint_and_distribute(
                target_agent_id=seller.id,
                amount=int(tx.total_pennies),
                tick=context.time,
                reason=f"bailout_{tx.id}"
            )

        elif tx.transaction_type == "bond_issuance":
             # Transfer: Agent (Buyer) -> Gov (Seller)
             return context.settlement_system.transfer(
                 debit_agent=buyer,
                 credit_agent=seller,
                 amount=int(tx.total_pennies),
                 memo=f"bond_issuance_{tx.id}",
                 tick=context.time
             ) is not None
        
        # ... existing logic ...
```

### 3.2. BankTransactionHandler (New)

```python
class BankTransactionHandler(ITransactionHandler):
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # Protocol Guards
        if not isinstance(seller, IBank) and tx.transaction_type == "bank_deposit":
             context.logger.error(f"Seller {seller.id} is not an IBank.")
             return False
        
        amount = int(tx.total_pennies)

        if tx.transaction_type == "bank_deposit":
            # Buyer (Agent) -> Seller (Bank)
            # 1. Transfer Cash
            success = context.settlement_system.transfer(
                debit_agent=buyer,
                credit_agent=seller,
                amount=amount,
                memo="deposit",
                tick=context.time
            )
            # 2. Update Ledger (if transfer success)
            if success:
                seller.record_deposit(buyer.id, amount)
            return success is not None

        elif tx.transaction_type == "bank_withdrawal":
            # Buyer (Agent) -> Seller (Bank) [Reverse Logic? Usually Seller gives money]
            # Convention: Buyer is always the 'Initiator' or 'Money Source'? 
            # Standard: Buyer pays, Seller receives. 
            # WITHDRAWAL: Agent wants money. Agent is "Buying" Cash? 
            # Let's stick to standard flow: Agent (Buyer) requests money from Bank (Seller).
            # BUT transaction represents Flow of Value. 
            # If Tx is "Withdrawal", Flow is Bank -> Agent.
            # So Buyer=Bank, Seller=Agent? Or Agent is Buyer of "Cash"?
            
            # DEFINITION: 
            # Buyer_ID = Source of Funds (Debit)
            # Seller_ID = Destination of Funds (Credit)
            # Wait, standard Transaction: Buyer PAYS Seller.
            
            # Case Withdrawal: Bank PAYS Agent.
            # Thus: Buyer = Bank, Seller = Agent.
            
            success = context.settlement_system.transfer(
                 debit_agent=buyer, # Bank
                 credit_agent=seller, # Agent
                 amount=amount,
                 memo="withdrawal",
                 tick=context.time
            )
            if success:
                 # Bank reduces internal ledger
                 # Note: Bank must be cast to IBank to access internal ledger methods
                 if isinstance(buyer, IBank):
                     buyer.record_withdrawal(seller.id, amount)
            return success is not None

        return False
```

---

## 4. Verification Plan

### 4.1. New Test Cases
- **`tests/systems/test_settlement_purity.py`**:
    - `test_transfer_rejects_float`: Pass `amount=100.5` -> Expect `TypeError`.
    - `test_get_engine_rejects_fake_agent`: Pass object with only `.id` -> Expect `TypeError`.
- **`tests/systems/handlers/test_monetary_handler_ext.py`**:
    - `test_bailout_execution`: Verify M2 increase and Agent balance update.
    - `test_bond_issuance_flow`: Verify Agent balance decrease, Gov balance increase.

### 4.2. Existing Impact
- **Mocks**: Any test in `tests/` using `MagicMock()` for agents without `spec=IAgent` will fail.
    - **Remediation**: Global Find/Replace `MagicMock()` -> `MagicMock(spec=IAgent)`.
- **TransactionProcessor**: Must update `register_handler` calls in `TransactionFactory` or `Bootstrap` logic.

### 4.3. Audit Check
- [x] **Zero-Sum**: All handlers use `SettlementSystem.transfer` or `mint/burn`.
- [x] **Protocols**: `isinstance` checks added.
- [x] **DTOs**: `Transaction` DTO used exclusively.

```

File: modules\finance\handlers\api.py
```python
from typing import Protocol, Any, runtime_checkable
from simulation.models import Transaction
from simulation.systems.api import TransactionContext

@runtime_checkable
class ITransactionHandler(Protocol):
    """
    Protocol for handling specific transaction types.
    Must be stateless and pure.
    """
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        """
        Executes the transaction logic.
        Args:
            tx: The transaction DTO.
            buyer: The entity paying (Debit).
            seller: The entity receiving (Credit).
            context: System context (Settlement, Registry, etc).
        Returns:
            bool: True if settlement was successful.
        """
        ...

@runtime_checkable
class IBankTransactionHandler(ITransactionHandler, Protocol):
    """
    Marker protocol for Bank-specific logic.
    """
    ...

@runtime_checkable
class IMonetaryPolicyHandler(ITransactionHandler, Protocol):
    """
    Marker protocol for Monetary Policy logic (CB/Gov).
    """
    ...

```