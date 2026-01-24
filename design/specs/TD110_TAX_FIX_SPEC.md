# Work Order: TD-110 Phantom Tax Fix Specification

**Phase:** 3 (Refinement)
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement

The system exhibits 'phantom tax revenue' where tax income is recorded even if the underlying fund transfer from the taxpayer fails. This is caused by the `TaxAgency.record_revenue` method, which logs statistics without verifying the transaction's success. The `Government.run_welfare_check` method generates `Transaction` objects for wealth tax, which are processed by a downstream system that incorrectly calls `record_revenue`, leading to data corruption.

## 2. Objective

Eliminate phantom tax revenue by enforcing an **atomic tax collection process**. All tax collection must be routed through a single, unified method that guarantees revenue is only recorded *after* a successful fund transfer. This refactoring will enforce a clear Separation of Concerns (SoC) between the `TaxAgency` and the `Government`.

## 3. Architectural Refactoring (SoC Enforcement)

To address the high coupling and dependency violations identified in the pre-flight audit, the following architectural changes are mandated:

### 3.1. `TaxAgency`: The Calculator & Orchestrator
- **Responsibility**: The `TaxAgency` is solely responsible for calculating tax amounts and orchestrating the collection by calling a provided settlement system.
- **Statelessness**: It will **no longer modify the `Government`'s state directly**. Its methods will be pure functions where possible or will return a result DTO.
- **Dependency Injection**: It will receive external system dependencies (like `ISettlementSystem`) as method parameters, not by accessing them through a `Government` object.

### 3.2. `Government`: The State Manager
- **Responsibility**: The `Government` agent is responsible for managing its own state (assets, revenue statistics).
- **Workflow**: It will call the `TaxAgency`'s methods, provide the necessary dependencies, receive a result DTO, and then update its own internal ledgers based on the verified outcome.

---

## 4. API & Interface Changes

### 4.1. [NEW] `modules/finance/api.py`: `TaxCollectionResultDTO`
A new DTO must be created to standardize the data returned by the collection process.

```python
# In modules/finance/api.py (or a suitable DTOs file)
from typing import TypedDict, Any

class TaxCollectionResult(TypedDict):
    """
    Represents the verified outcome of a tax collection attempt.
    """
    success: bool
    amount_collected: float
    tax_type: str
    payer_id: Any
    payee_id: Any
    error_message: str | None
```

### 4.2. [REFACTOR] `simulation/systems/tax_agency.py`
The `TaxAgency` will be refactored to be a stateless service.

```python
# In simulation/systems/tax_agency.py
import logging
from typing import Any
from simulation.interfaces.finance_interface import ISettlementSystem # Assuming this interface exists
from modules.finance.api import TaxCollectionResult # Import the new DTO

logger = logging.getLogger(__name__)

class TaxAgency:
    def __init__(self, config_module):
        self.config_module = config_module

    # ... existing calculate_* methods remain unchanged ...

    @DeprecationWarning
    def record_revenue(self, government, amount: float, tax_type: str, payer_id: Any, current_tick: int):
        """
        [DEPRECATED] This method is the source of phantom revenue and will be removed.
        All logic is merged into the new atomic collect_tax method.
        """
        logger.warning("DEPRECATED: TaxAgency.record_revenue called. Use atomic collect_tax instead.")
        pass

    def collect_tax(
        self,
        payer: Any,
        payee: Any,
        amount: float,
        tax_type: str,
        settlement_system: ISettlementSystem,
        current_tick: int
    ) -> TaxCollectionResult:
        """
        [NEW & UNIFIED] Atomically collects tax by executing a transfer and only
        returning a success result if the transfer is confirmed. This method does
        NOT modify any agent's state.

        Args:
            payer: The entity paying the tax (must have .id and be compatible with ISettlementSystem).
            payee: The entity receiving the tax (must have .id).
            amount: The amount of tax to be collected.
            tax_type: The type of tax (e.g., 'wealth_tax', 'corporate_tax').
            settlement_system: The system responsible for executing the fund transfer.
            current_tick: The current simulation tick.

        Returns:
            A TaxCollectionResult DTO with the outcome of the transaction.
        """
        if amount <= 0:
            return TaxCollectionResult(success=True, amount_collected=0.0, tax_type=tax_type, payer_id=payer.id, payee_id=payee.id, error_message=None)

        # 1. Attempt the fund transfer via the injected settlement system.
        transfer_success = settlement_system.transfer(
            sender=payer,
            recipient=payee,
            amount=amount,
            memo=f"{tax_type} collection"
        )

        # 2. Verify the outcome.
        if not transfer_success:
            logger.warning(f"TAX_COLLECTION_FAILED | Tick {current_tick} | Failed to collect {amount:.2f} of {tax_type} from {payer.id} to {payee.id}")
            return TaxCollectionResult(
                success=False,
                amount_collected=0.0,
                tax_type=tax_type,
                payer_id=payer.id,
                payee_id=payee.id,
                error_message="Insufficient funds or transfer failed."
            )

        # 3. On success, return a result DTO with the collected amount.
        logger.info(f"TAX_COLLECTION_SUCCESS | Tick {current_tick} | Collected {amount:.2f} of {tax_type} from {payer.id}")
        return TaxCollectionResult(
            success=True,
            amount_collected=amount,
            tax_type=tax_type,
            payer_id=payer.id,
            payee_id=payee.id,
            error_message=None
        )

```

### 4.3. [REFACTOR] `simulation/agents/government.py`
The `Government` agent must be updated to use the new synchronous, atomic collection process.

#### `Government.run_welfare_check`
The logic for generating `Transaction` objects for wealth tax will be **removed** and replaced with a direct, synchronous call.

```python
# In simulation/agents/government.py -> run_welfare_check method

# ... inside the loop over agents ...

# A. Wealth Tax (REFACTORED LOGIC)
net_worth = agent.assets
if net_worth > wealth_threshold:
    tax_amount = (net_worth - wealth_threshold) * wealth_tax_rate_tick
    tax_amount = min(tax_amount, agent.assets)

    if tax_amount > 0:
        # --- REMOVE THIS BLOCK ---
        # tx = Transaction(...)
        # transactions.append(tx)
        # --- END REMOVED BLOCK ---

        # --- ADD THIS BLOCK ---
        result = self.tax_agency.collect_tax(
            payer=agent,
            payee=self,
            amount=tax_amount,
            tax_type="wealth_tax",
            settlement_system=self.settlement_system, # Pass the dependency
            current_tick=current_tick
        )

        # Government updates its OWN state based on the verified result
        if result['success']:
            self.total_collected_tax += result['amount_collected']
            self.revenue_this_tick += result['amount_collected']
            self.tax_revenue['wealth_tax'] = self.tax_revenue.get('wealth_tax', 0.0) + result['amount_collected']
            # ... and so on for other statistics ...
        # --- END ADDED BLOCK ---
```

#### `Government.record_revenue`
This method becomes a simple state-updating helper.

```python
# In simulation/agents/government.py

def record_revenue(self, result: TaxCollectionResult):
    """
    [NEW] Updates the government's internal ledgers based on a verified
    TaxCollectionResult DTO.
    """
    if not result['success'] or result['amount_collected'] <= 0:
        return

    amount = result['amount_collected']
    tax_type = result['tax_type']

    self.total_collected_tax += amount
    self.revenue_this_tick += amount
    self.tax_revenue[tax_type] = (
        self.tax_revenue.get(tax_type, 0.0) + amount
    )
    # ... update other stats as needed ...
```
The logic inside `run_welfare_check` can then be simplified to call `self.record_revenue(result)`.

## 5. Implementation & Verification Plan

1.  **Phase 1: API Definition**:
    - [ ] Create `TaxCollectionResult` TypedDict in `modules/finance/api.py`.

2.  **Phase 2: `TaxAgency` Refactor**:
    - [ ] Mark the old `record_revenue` as deprecated.
    - [ ] Implement the new, unified `collect_tax` method as specified above, ensuring it is stateless.

3.  **Phase 3: `Government` Refactor**:
    - [ ] Modify `Government.run_welfare_check` to remove `Transaction` generation for wealth tax.
    - [ ] Implement the new synchronous call to `tax_agency.collect_tax`.
    - [ ] Implement the `Government.record_revenue(result: TaxCollectionResult)` helper method.
    - [ ] Ensure the `Government` updates its state *only* after a successful result from `collect_tax`.

4.  **Phase 4: Verification**:
    - [ ] **Crucial**: Review and remove any logic in the main simulation loop (`TransactionProcessor`) that handles `transaction_type="tax"`, as this is now obsolete.
    - [ ] Write a new unit test, `test_atomic_wealth_tax_collection`, which confirms that a household's assets are debited, the government's assets are credited, and revenue is recorded correctly.
    - [ ] Write a new unit test, `test_failed_wealth_tax_collection`, where the household has insufficient funds. Verify that the government's assets and revenue statistics do **not** change.
    - [ ] Run the full test suite (`pytest`) to check for regressions, especially in corporate tax collection which may also need to be updated to use this new pattern.

## 6. Risk & Impact Analysis

-   **Architectural Improvement**: This change correctly enforces Separation of Concerns, making `TaxAgency` a reusable, stateless service and `Government` the sole manager of its state. This reduces coupling and makes the system more robust.
-   **Dependency Inversion**: By injecting `ISettlementSystem`, the `TaxAgency` no longer violates the Law of Demeter. Its dependencies are explicit.
-   **Process Change (Async to Sync)**: The collection of wealth tax is now a synchronous, immediate operation within `Government.run_welfare_check`. This is a significant but necessary architectural shift to eliminate the bug. All downstream logic and tests that relied on the asynchronous `Transaction` for wealth tax are now invalid and must be removed or updated.

---

### 🚨 Mandatory Reporting Clause

As the developer (Jules) implementing this specification, you are required to document any unforeseen challenges, insights, or newly discovered technical debt. Create a markdown file in `communications/insights/` named `TD110-Fix-Insights-<your_name>.md` and log your findings. If any part of this specification proves infeasible, escalate immediately by creating a request in `communications/requests/`.
