file: modules/system/transactions/api.py
```python
from __future__ import annotations
from typing import Protocol, List, Optional, Any, runtime_checkable, TypedDict
from dataclasses import dataclass
from modules.simulation.api import AgentID
from modules.finance.dtos import MoneyDTO
from modules.system.api import CurrencyCode

# DTOs
@dataclass(frozen=True)
class TransactionResultDTO:
    """
    Standardized result object for any transaction execution.
    Replaces ad-hoc boolean/tuple returns.
    """
    success: bool
    transaction_id: str
    amount_settled: int
    currency: CurrencyCode
    tax_paid: int = 0
    fees_paid: int = 0
    resulting_log: Optional[str] = None
    error_code: Optional[str] = None

class EscrowContextDTO(TypedDict):
    """Context required for 3-step escrow transactions (Goods)."""
    buyer_id: AgentID
    seller_id: AgentID
    item_id: str
    total_amount_pennies: int
    tax_amount_pennies: int
    escrow_agent_id: AgentID

# Protocols
@runtime_checkable
class ITransactionHandler(Protocol):
    """
    Protocol for a specialized transaction handler.
    Follows the Strategy Pattern for TransactionProcessor.
    """
    def handle(
        self,
        transaction: Any, # Transaction Model
        buyer: Any,       # Agent/Entity
        seller: Any,      # Agent/Entity
        context: Any      # TransactionContext
    ) -> bool:
        """
        Executes the business logic for a specific transaction type.
        Must return True if successful, False otherwise.
        Should handle its own side-effects via the Context (Settlement, Registry).
        """
        ...

@runtime_checkable
class IEscrowService(Protocol):
    """
    Interface for handling secure escrow exchanges.
    Decoupled from the monolithic TransactionManager.
    """
    def execute_secured_trade(
        self,
        ctx: EscrowContextDTO,
        settlement_system: Any,
        government: Any
    ) -> TransactionResultDTO:
        """
        Executes a trade: Buyer -> Escrow -> (Seller + Tax).
        Must guarantee atomicity (all-or-nothing).
        """
        ...

@runtime_checkable
class ITaxCalculator(Protocol):
    """
    Interface for calculating taxes during transaction processing.
    """
    def calculate_tax(
        self,
        transaction_type: str,
        amount_pennies: int,
        payer: Any,
        payee: Any,
        context: Any
    ) -> int:
        ...

```

file: design/3_work_artifacts/specs/transaction_unification_spec.md
```markdown
# Spec: Transaction Logic Unification (TD-PROC-TRANS-DUP)

## 1. Introduction
This specification outlines the strategy to deprecate the legacy `TransactionManager` and consolidate all transaction processing logic into the modular `TransactionProcessor`. This resolves **TD-PROC-TRANS-DUP** and aligns with the **SEO (Stateless Engine & Orchestrator)** pattern.

### 1.1. Goals
- **Single Source of Truth**: One pipeline for all value transfers.
- **Modularity**: Replace monolithic `if/elif` blocks with `ITransactionHandler` strategies.
- **Safety**: Preserve the "Escrow" logic for Goods and "Withholding" logic for Labor.
- **Type Safety**: Enforce `int` pennies usage throughout the pipeline.

---

## 2. Architecture & Components

### 2.1. The `TransactionProcessor` (Updated)
The `TransactionProcessor` remains the orchestrator but will be enhanced to support:
- **Handler Registry**: A map of `transaction_type` -> `ITransactionHandler`.
- **Fallback Logic**: A default handler for simple transfers.
- **Context Injection**: Providing `SettlementSystem`, `TaxationSystem`, and `Registry` to handlers.

### 2.2. Specialized Handlers
We will extract logic from `TransactionManager` into the following handlers:

| Transaction Type | New Handler Class | Responsibility |
| :--- | :--- | :--- |
| `goods` | `GoodsTransactionHandler` | Implements 3-step Escrow (Buyer->Escrow->Seller/Gov). Handles Sales Tax. |
| `labor`, `research_labor` | `LaborTransactionHandler` | Handles Income Tax calculation and withholding. Supports Firm vs Household payers. |
| `omo_purchase`, `omo_sale` | `MonetaryPolicyHandler` | Handles Central Bank minting/burning operations. |
| `lender_of_last_resort` | `MonetaryPolicyHandler` | CB Minting to Banks. |
| `escheatment` | `FiscalTransactionHandler` | Asset seizure/transfer to Government. |
| `dividend`, `interest` | `FinancialTransactionHandler` | Simple transfers, potentially with capital gains tax hooks (future). |

---

## 3. Detailed Design

### 3.1. `GoodsTransactionHandler` (Escrow Logic)
**Logic Flow:**
1.  **Calculate Totals**: Price * Quantity.
2.  **Calculate Tax**: `round_to_pennies(total * sales_tax_rate)`.
3.  **Solvency Check**: `buyer.balance >= total + tax`.
4.  **Step 1 (Lock)**: Transfer `total + tax` from Buyer to `EscrowAgent`.
    - *Fail*: Return False.
5.  **Step 2 (Distribute)**:
    - Transfer `total` from `EscrowAgent` to Seller.
    - Transfer `tax` from `EscrowAgent` to Government.
    - *Fail*: Rollback (Transfer all from Escrow back to Buyer).
6.  **Registry Update**: Call `registry.update_ownership()`.

### 3.2. `LaborTransactionHandler` (Withholding)
**Logic Flow:**
1.  **Determine Survival Cost**: Based on `market_data` (Food Price).
2.  **Calculate Tax**: Call `government.calculate_income_tax(wage, survival_cost)`.
3.  **Transfer Wage**:
    - If Payer is Firm: Transfer `wage` to Household. Then Firm pays `tax` to Gov.
    - If Payer is Household: Transfer `wage` to Worker. Then Worker pays `tax` to Gov.
4.  **Employment Update**: Update `is_employed` status in `AgentState`.

### 3.3. `MonetaryPolicyHandler`
**Logic Flow:**
1.  **Type Check**: Identify `omo_purchase` (Mint) vs `omo_sale` (Burn).
2.  **Execution**: Call `central_bank.mint_and_transfer` or `central_bank.transfer_and_burn`.
3.  **Audit**: Verify M2 supply impact via `central_bank.audit_total_m2()`.

---

## 4. Migration Plan

### Phase 1: Handler Implementation
- Create `modules/system/transactions/handlers/` directory.
- Implement `GoodsTransactionHandler`, `LaborTransactionHandler`, etc.
- **Golden Test**: Create a test suite that feeds the same `Transaction` DTO to both `TransactionManager` (Legacy) and `TransactionProcessor` (New) and asserts identical ledger states.

### Phase 2: Wiring
- In `simulation/systems/system_factory.py`, inject the new handlers into `TransactionProcessor`.
- Ensure `TransactionProcessor` has access to `EscrowAgent` (required for Goods).

### Phase 3: Switchover
- Update `Simulation.run_tick()` to call `transaction_processor.execute()` instead of `transaction_manager.execute()`.
- **Flag**: Use a config flag `USE_UNIFIED_PROCESSOR = True` for safe rollback.

### Phase 4: Cleanup
- Delete `TransactionManager`.
- Remove `USE_UNIFIED_PROCESSOR` flag.

---

## 5. Verification & Risk

### 5.1. Risk Analysis (Pre-Implementation)
- **Risk**: Escrow Rollback Failure.
    - *Mitigation*: The `SettlementSystem` must be atomic or the Handler must implement robust `try/except` rollback blocks (as legacy does).
- **Risk**: Tax Calculation Drift.
    - *Mitigation*: Ensure `round_to_pennies` is used identically.
- **Risk**: Reference Cycles.
    - *Mitigation*: Handlers must receive Agents via `TransactionContext`, not store them.

### 5.2. Verification Plan
- **Unit Tests**:
    - `test_goods_handler_escrow_success`: Verify funds move Buyer->Escrow->Seller/Gov.
    - `test_goods_handler_insufficient_funds`: Verify no movement.
    - `test_labor_handler_tax_withholding`: Verify correct tax split.
- **Integration Tests**:
    - Run `simulation_test.py` with `USE_UNIFIED_PROCESSOR=True`.
    - Compare `trace_output.txt` with legacy trace.

### 5.3. Debt Audit
- **Resolves**: TD-PROC-TRANS-DUP.
- **Resolves**: TD-CRIT-FLOAT-SETTLE (Partial - enforces int usage in handlers).
```

file: communications/insights/transaction-unification-spec.md
```markdown
# Insight: Transaction Unification Specification

**Mission Key**: transaction-unification-spec
**Date**: 2026-02-17
**Author**: Gemini Scribe

## 🏗️ Architectural Insights

### 1. The Redundancy Problem (TD-PROC-TRANS-DUP)
I confirmed that `TransactionManager.py` and `TransactionProcessor.py` currently coexist with overlapping responsibilities. `TransactionManager` contains vital business logic (Escrow, Tax) that `TransactionProcessor`'s current default handler lacks. The unification strategy effectively treats `TransactionManager`'s logic blocks as "Strategy" implementations to be injected into `TransactionProcessor`.

### 2. The Escrow Complexity
The legacy code performs a manual "3-step escrow" within the manager.
- **Current**: Manager manually calls `settlement.transfer` 3 times.
- **New**: `GoodsTransactionHandler` will encapsulate this.
- **Insight**: Ideally, `SettlementSystem` should support an atomic `transfer_multi_leg` or `escrow_transfer` method to remove this logic from the handler layer entirely. For now, we replicate the logic in the Handler to minimize regression risk, but I've noted this as a potential future refactor.

### 3. Float-to-Int Compliance
The legacy `TransactionManager` uses `int(tx.quantity * tx.price)` casting.
The new spec enforces `round_to_pennies()` which is safer. This might cause a 1-penny variance in regression tests compared to the legacy system if the legacy system was truncating floors instead of rounding.
- **Action**: The spec mandates `round_to_pennies` consistent with `modules.finance.utils`.

## ⚠️ Identified Risks

- **Implicit Dependencies**: The legacy manager accesses `state.market_data` directly for food prices. The new `TransactionContext` must ensure `market_data` is freshly populated before handlers run.
- **Public Manager Hijacking**: `TransactionProcessor` currently has a "Public Manager Hijack" block. This needs to be formalized into a registered `PublicSectorHandler` to avoid hardcoded `if seller_id == "PUBLIC_MANAGER"` checks in the main loop.

## 🧪 Verification Strategy

I have outlined a "Parallel Run" test strategy where we can execute both processors on a copied state and diff the results.

```python
# Pseudo-code for Verification
def test_parity(transaction, state):
    state_legacy = state.clone()
    state_new = state.clone()
    
    legacy_mgr.execute(state_legacy)
    new_proc.execute(state_new)
    
    assert state_legacy.ledger == state_new.ledger
```

This confirms logical equivalence before we delete the legacy code.
```