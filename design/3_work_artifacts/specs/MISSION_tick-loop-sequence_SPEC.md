File: communications/insights/audit-tick-loop-sequence.md
```markdown
# Architectural Insight: Tick Loop Sequence Audit (Mission: audit-tick-loop-sequence)

## 1. Executive Summary
This audit addresses the critical blocker in Phase 18 regarding Corporate Tax calculation. The current architecture faces a circular dependency where Tax calculation depends on "Realized Profit" (Revenue - Cost), but Revenue is only realized *after* the Unified Transaction Phase (Phase 3). Since the Transaction Phase is the only settlement point, Tax cannot be calculated *and* settled in the same tick using real-time data without splitting the settlement phase.

**Decision:** We will adopt a **Lagged Tax Calculation (T-1)** model. Corporate Tax for Tick `T` will be calculated based on the *Realized Financial Performance* of Tick `T-1`. This adheres to the **SEO Pattern** and **Financial Integrity** standards by relying on settled, immutable history rather than volatile intents.

## 2. Architectural Analysis

### 2.1. The Contradiction
- **Documentation (`HANDOVER.md`)**: States `firm.produce()` occurs *after* the unified transaction phase.
- **Code (`tick_orchestrator.py`)**: Shows `Phase_Production` (Index 3) occurs *before* `Phase3_Transaction` (Index 14).
- **Root Cause**: The confusion likely stems from the distinction between *Production* (creation of goods) and *Revenue Realization* (sales). While goods are produced early, the *Profit* (basis for tax) is only known after `Phase3_Transaction` executes trades.

### 2.2. The Dependency Cycle
1.  **Revenue Realization**: Happens in `Phase3_Transaction` (Settlement).
2.  **Tax Calculation**: Requires Revenue.
3.  **Tax Payment**: Must happen in `Phase3_Transaction` (to be unified).
4.  **Conflict**: `Phase3` cannot execute a Tax Payment that hasn't been calculated yet, and Tax cannot be calculated on `Phase3` results before `Phase3` runs.

### 2.3. Solution: Lagged Tax (T-1)
By decoupling the *Calculation Basis* (T-1) from the *Payment Execution* (T), we resolve the cycle.
- **Tick T-1**: Firm earns Profit. End-of-tick accounting records this in `FinancialHistory`.
- **Tick T**: `Phase_TaxationIntents` reads `FinancialHistory[T-1]`. Generates `TaxTransaction`.
- **Tick T**: `Phase3_Transaction` executes `TaxTransaction`.

## 3. Impact Analysis

- **Zero-Sum Integrity**: ✅ Preserved. Tax is based on settled funds.
- **Component Purity**: ✅ `TaxationSystem` remains stateless, reading from `Firm` state DTOs.
- **Tick 1 Leak Risk**: ⚠️ Tick 0 has no history. Logic must handle `T=0` explicitly (Tax = 0).
- **DTO Changes**: `FirmStateDTO` must include `financial_history` or `last_tick_profit`.

## 4. Test Evidence
*[Test Evidence]: N/A (Scribe Mode - Pending Implementation)*
- **Planned Verification**:
    - `test_taxation_lagged_calculation`: Verify tax is 0 on Tick 0, and correct on Tick 1 based on Tick 0 profit.
    - `test_firm_financial_history`: Verify `Firm` correctly aggregates P&L at end of tick.
```

File: design/3_work_artifacts/specs/tick_resequencing_spec.md
```markdown
# Specification: Tick Loop Resequencing & Lagged Tax

## 1. Introduction
- **Purpose**: Resolve the circular dependency between Realized Profit and Corporate Tax Calculation to enable the activation of Corporate Tax logic.
- **Scope**: `TickOrchestrator`, `Phase_TaxationIntents`, `Firm` (Financial Recording), and `TaxationSystem`.
- **Standards**: [SEO_PATTERN.md](../../1_governance/architecture/standards/SEO_PATTERN.md), [FINANCIAL_INTEGRITY.md](../../1_governance/architecture/standards/FINANCIAL_INTEGRITY.md).

## 2. Architectural Changes

### 2.1. The Lagged Tax Model
Corporate Tax is calculated on the *Realized Profit* of the **previous tick (T-1)**. This allows the Tax Transaction for Tick `T` to be generated early in the loop and settled in the Unified Transaction Phase alongside other trades.

### 2.2. New Tick Sequence
The `TickOrchestrator` phases are re-affirmed with clear data dependencies:

1.  **Phase 0: Production & System** (`Phase_Production`)
    - Firms produce goods. Inventory updates. Cost (Input Goods) recorded.
2.  **Phase 1: Decision** (`Phase1_Decision`)
    - Agents plan.
3.  **Phase 2: Matching** (`Phase2_Matching`)
    - Markets generate `Trade` intents.
4.  **Phase 3: Operational Intents** (`Phase_FirmProductionAndSalaries`)
    - Firms generate Salary intents.
5.  **Phase 4: Fiscal Calculation** (`Phase_TaxationIntents`)
    - **Logic**: Retrieve `Firm.financial_record[T-1]`. Calculate Tax. Generate `TaxTransaction`.
    - **Input**: `SimulationState.firms` (with history).
    - **Output**: `SimulationState.transactions` (appended).
6.  **Phase 5: Unified Settlement** (`Phase3_Transaction`)
    - **Logic**: Execute all intents (Trades, Salaries, Taxes).
    - **Result**: Balances updated. Revenue/Expense realized.
7.  **Phase 6: Accounting (New/Explicit)** (`Phase_Accounting` or `Finalize`)
    - **Logic**: Aggregate current tick's Revenue/Cost for each Firm. Update `Firm.financial_record[T]`.

### 2.3. Data Structures

#### `FinancialRecordDTO` (New)
```python
@dataclass(frozen=True)
class FinancialRecordDTO:
    tick: int
    gross_revenue: int
    cogs: int  # Cost of Goods Sold
    wages_paid: int
    tax_paid: int
    net_profit: int
```

#### `IFinancialEntity` (Update)
- Add `get_financial_record(tick: int) -> Optional[FinancialRecordDTO]`

## 3. Detailed Logic

### 3.1. Firm Accounting (End of Tick)
- In `_finalize_tick` (or a dedicated phase), the system must aggregate:
    - **Revenue**: Sum of all *successful* `Trade` transactions where `seller == firm`.
    - **COGS**: Sum of input goods cost (tracked during Production).
    - **Wages**: Sum of *successful* Salary transactions.
- This requires the `TransactionProcessor` to return a `Receipt` or `Ledger` that can be queried by Agent ID.

### 3.2. Taxation System
```python
def generate_corporate_tax_intents(self, firms: List[IFirm], current_tick: int) -> List[Transaction]:
    intents = []
    if current_tick == 0:
        return []  # No history

    for firm in firms:
        # Lagged Lookup
        record = firm.get_financial_record(current_tick - 1)
        if not record or record.net_profit <= 0:
            continue

        tax_amount = self._calculate_tax(record.net_profit)
        if tax_amount > 0:
            intents.append(self._create_tax_tx(firm, tax_amount))
    return intents
```

## 4. Verification Plan

### 4.1. New Test Cases
- **`test_taxation_lagged_logic`**:
    - Setup: Mock Firm with `FinancialRecord(tick=1, net_profit=1000)`.
    - Action: Run `TaxationSystem` for `tick=2`.
    - Assert: Tax Transaction generated for correct amount.
- **`test_firm_accounting_aggregation`**:
    - Setup: Firm executes 1 Trade (Sale) and 1 Salary payment.
    - Action: Run End-of-Tick Accounting.
    - Assert: `FinancialRecord` reflects correct Profit.

### 4.2. Impact on Existing Tests
- Existing tests using `Phase_TaxationIntents` might fail if they expect T-0 tax.
- **Action**: Update fixtures to seed `financial_history` if T-0 tax is being tested (unlikely).

## 5. Risk & Mitigation
- **Risk**: `TransactionProcessor` currently might not return structured data per-agent easily.
- **Mitigation**: Update `TransactionProcessor.execute` to return a `BatchResult` containing a map of `AgentID -> FinancialSummary`.
- **Risk**: Tick 0 has no tax.
- **Mitigation**: Acceptable. Simulation warmup usually ignores T-0 financials.
```

File: modules/simulation/orchestration/phases/resequenced_api.py
```python
"""
Draft API for Resequenced Phases and Financial Recording
Target: modules/simulation/orchestration/phases/api.py (Draft)
"""
from typing import Protocol, List, Optional, Dict
from dataclasses import dataclass
from simulation.dtos.api import Transaction, SimulationState

@dataclass(frozen=True)
class FinancialRecordDTO:
    """
    Immutable record of an agent's financial performance for a specific tick.
    Used for Lagged Tax Calculation.
    """
    tick: int
    gross_revenue: int
    cogs: int
    wages_paid: int
    tax_paid: int
    net_profit: int

class IFinancialHistoryHolder(Protocol):
    """
    Protocol for agents that maintain financial history for taxation.
    """
    @property
    def id(self) -> str: ...
    
    def get_financial_record(self, tick: int) -> Optional[FinancialRecordDTO]:
        """Retrieve the finalized financial record for a specific tick."""
        ...

    def record_tick_financials(self, record: FinancialRecordDTO) -> None:
        """Called by the Orchestrator/AccountingSystem at end of tick."""
        ...

class IPhaseStrategy(Protocol):
    """
    Standard Interface for all Tick Phases.
    Must adhere to SEO_PATTERN.
    """
    def execute(self, state: SimulationState) -> SimulationState:
        ...

class ITaxationSystem(Protocol):
    """
    Interface for the Taxation Domain Service.
    """
    def generate_corporate_tax_intents(
        self, 
        firms: List[IFinancialHistoryHolder], 
        current_tick: int
    ) -> List[Transaction]:
        """
        Calculates tax based on T-1 FinancialRecord.
        Returns a list of Transaction intents (not executed).
        """
        ...
```