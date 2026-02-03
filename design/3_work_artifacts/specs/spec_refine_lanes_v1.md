# WO-116-B Spec Formalization: Atomic Transaction Generation

## 1. Objective

This document provides the formalized specification for Work Order 116, Phase B. The primary goal is to refactor all systemic, non-market asset transfers into a **declarative, atomic transaction generation** model. This eliminates direct state modifications and centralizes all financial settlements within the `TransactionProcessor`, ensuring 100% zero-sum integrity as mandated by `platform_architecture.md`.

This formalized spec supersedes the draft in `WO116_PHASE_B_SPEC.md` and incorporates the strict atomicity principles from `SPEC_TAX_DECOUPLING_SAGA_V2.md`.

## 2. Core Architectural Changes

### 2.1. Firm Production Re-sequencing
The firm production loop (`firm.produce()`) is moved to execute *before* the Sacred Sequence. This decouples profit calculation from the current tick's decision-making, providing a stable basis for transaction generation. This change remains as specified in the original draft.

### 2.2. Transaction Generation Model
All system-level modules (e.g., `Bank`, `Government`, `FinanceSystem`) that perform financial transfers will be refactored. Their methods will no longer call the `SettlementSystem` directly. Instead, they will return a `List[TransactionDTO]` or a similar data transfer object. A central orchestrator, `TickScheduler`, will collect these transaction intents and pass them to the `TransactionProcessor` for atomic execution.

## 3. Formalized Implementation Plan

The following sections detail the required refactoring, using Corporate Tax collection as the blueprint. This pattern must be applied to all other system-level financial operations (interest payments, profit distribution, welfare, etc.).

### 3.1. [REMOVED] Direct Asset Modification
All direct calls to `_sub_assets` or `_add_assets` for inter-agent transfers are strictly forbidden and must be removed.

### 3.2. [FORMALIZED] Corporate Tax Collection

The flawed logic in the original draft is replaced with a robust, two-step process: **Intent Generation** and **Post-Settlement Recording**.

**Location:** `simulation/tick_scheduler.py` (within `run_tick`)

**New Formalized Logic:**

```python
# In TickScheduler.run_tick, before the Sacred Sequence

# ... (other system transaction generation) ...

# [FORMALIZED] Corporate Tax Intent Generation
# The TickScheduler now orchestrates tax calculation via a dedicated system.
system_transactions: List[TransactionDTO] = []
tax_intents = state.taxation_system.generate_corporate_tax_intents(state.firms)
system_transactions.extend(tax_intents)

# ... (rest of Sacred Sequence) ...


def _phase_transactions(self, state: SimulationState, system_transactions: List[TransactionDTO]) -> None:
    """Phase 3: Atomically execute all market and system transactions."""
    
    # 1. Combine all transaction intents for the tick
    all_intents = state.market_transactions + system_transactions
    
    # 2. Settle all transactions atomically
    # The processor is responsible for calling the SettlementSystem and handling results.
    settlement_results = self.world_state.transaction_processor.execute(all_intents, state)
    
    # 3. [NEW] Record the outcomes of tax transactions (Saga Pattern)
    # The processor returns results, which are now used for safe bookkeeping.
    state.taxation_system.record_revenue(settlement_results)
```

This new flow ensures:
1.  The `TickScheduler` only generates *intents*. It doesn't know the outcome.
2.  The `TransactionProcessor` executes all intents.
3.  The `TaxationSystem` records revenue *only after* receiving confirmation of success from the `TransactionProcessor`, eliminating phantom revenue.

### 3.3. [NEW] `TaxationSystem` API (`modules/government/taxation/api.py`)

To support this, a `TaxationSystem` is required. If not already present, it must be created with the following API.

```python
# modules/government/taxation/api.py
from typing import Protocol, List, Dict
from core.dtos import TransactionDTO, SettlementResultDTO

class ITaxationSystem(Protocol):
    """
    Interface for the system responsible for all tax calculation and revenue recording.
    This system is the single source of truth for tax policy and ledgers.
    """

    def generate_corporate_tax_intents(self, firms: List[Any]) -> List[TransactionDTO]:
        """
        Calculates corporate tax for all eligible firms and returns transaction intents.
        This method is purely computational and does not modify any state.
        
        It reads tax parameters from the config system.
        """
        ...

    def record_revenue(self, results: List[SettlementResultDTO]) -> None:
        """
        Records the outcome of tax payments in the government's ledgers.
        This method is called *after* settlement has occurred.
        It updates ledgers only for transactions marked as successful.
        """
        ...
```

### 3.4. [NEW] `economy_params.yaml` Configuration

All hardcoded tax values must be externalized. The `TaxationSystem` will rely on these configuration values.

**File:** `config/economy_params.yaml`

```yaml
# config/economy_params.yaml
taxation:
  corporate_tax_rate: 0.21  # Example: 21% corporate tax
  # Add other tax rates here (income, wealth, sales)
  # e.g., sales_tax_rate: 0.05
```

## 4. Verification Plan

1.  **Zero-Sum Integrity**: The primary success metric remains the end-of-tick zero-sum audit (`scripts/audit_zero_sum.py`). It must pass with zero deviation.
2.  **Behavioral Unit Tests**: All unit tests must be refactored to the "Behavior Verification" pattern. They will check that a method returns the correct `TransactionDTO` list, not that it changed an agent's state.
3.  **New `TaxationSystem` Tests**:
    *   `test_tax_intent_calculation`: Verify that `generate_corporate_tax_intents` correctly calculates tax amounts based on firm profits and the `corporate_tax_rate` from the config.
    *   `test_record_revenue_success`: Provide a successful `SettlementResultDTO` and assert that the internal tax ledger is correctly updated.
    *   `test_record_revenue_failure`: Provide a failed `SettlementResultDTO` and assert that the ledger remains unchanged.

## 5. Risk & Impact Audit

This formalized specification addresses all identified architectural risks:

1.  **SRP Violation**: **Mitigated**. The `Government` agent is no longer responsible for tax calculation or collection. The `TaxationSystem` handles all tax logic. The `TickScheduler` orchestrates. The `TransactionProcessor` executes.
2.  **"Magic Money" / Leaks**: **Eliminated**. By removing all direct asset modifications and centralizing settlement, the risk of phantom revenue or money leaks from failed partial transactions is eliminated. The process is fully atomic.
3.  **Configuration Brittleness**: **Mitigated**. All tax rates are now defined in `config/economy_params.yaml`, allowing for easy modification without code changes.
4.  **Test Invalidation**: **Acknowledged**. The verification plan explicitly requires a shift to behavior-driven testing, which is a necessary consequence of this architectural improvement.

---

## 🚨 Mandatory Reporting
During implementation, log all findings in `communications/insights/WO-116-Formalization-Log.md`. Any newly discovered architectural debt must be recorded in `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`.
