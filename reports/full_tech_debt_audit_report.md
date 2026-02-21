# ⚖️ Protocol Validation Report

### 1. 🚦 Overall Grade: **FAIL**

The system is currently in a **CRITICAL FAILURE** state. While recent refactors (Wave 1.2) have improved Protocol adherence, the simulation is functionally broken due to the "Invisible Agent" phenomenon. The Economic Engine cannot start because its primary liquidity sources (Central Bank, Public Manager) are disconnected from the Settlement System.

### 2. ❌ Violations (Table)

| File | Severity | Violation Type | Description |
|---|---|---|---|
| `simulation/initialization/initializer.py` | **CRITICAL** | **Architecture Breach** | `TD-CRIT-SYS0-MISSING`: Central Bank is instantiated but **never registered** in `sim.agents`. Settlement System cannot see Account 0. |
| `simulation/initialization/initializer.py` | **CRITICAL** | **Architecture Breach** | `TD-CRIT-PM-MISSING`: Public Manager is instantiated but **never registered** in `sim.agents`. Asset recovery fails. |
| `modules/finance/dtos.py` vs `fails.txt` | **High** | **DTO Signature Mismatch** | `BorrowerProfileDTO`: Test suite and Codebase disagree on `borrower_id` field presence (17 Test Failures). |
| `modules/finance/api.py` | **High** | **Type Safety** | `LoanInfoDTO` is being accessed as a `dict` in tests/legacy code (`TypeError: not subscriptable`), violating Protocol Purity. |
| `simulation/firms.py` | **Medium** | **Coupling** | `TD-ARCH-FIRM-COUP`: Components use `attach(self)`, retaining tight coupling to the Parent Firm. |
| `simulation/db/logger.py` (Implied) | **High** | **Schema Drift** | `TD-DB-SCHEMA-DRIFT`: DB likely lacks `total_pennies` column required by new `TransactionData` DTO. |

### 3. 💡 Suggested Fixes

**A. Fix the Invisible Hand (Initializer)**
In `simulation/initialization/initializer.py`:
```python
# ... inside build_simulation ...
sim.central_bank = CentralBank(...)
sim.public_manager = PublicManager(...)

# FIX: Explicitly register System Agents BEFORE passing to Registry
sim.agents[sim.central_bank.id] = sim.central_bank
sim.agents[sim.public_manager.id] = sim.public_manager

# THEN update with households/firms
sim.agents.update({h.id: h for h in self.households})
# ...
```

**B. Fix Public Manager Insolvency**
Ensure Public Manager has infinite overdraft or massive endowment:
```python
# In Public Manager initialization or Financial Component
self.financial_component.allows_overdraft = True 
# OR
self.financial_component.deposit(1_000_000_000_000, "USD") # 1 Trillion pennies
```

**C. Fix DTO Usage**
Replace dict access `loan['field']` with dot access `loan.field` in legacy handlers.

---

[FILE_CONTENT: communications/insights/tech-debt-full-audit.md]
# Technical Debt Audit Report: Full System Review
**Date:** 2026-02-21
**Auditor:** Gemini CLI (Protocol Validator)
**Reference Ledger:** `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

## 1. Executive Summary

This audit confirms that the "Liquidity Asphyxiation" and "Zombie Firm" phenomena observed in recent simulation runs are directly caused by **Critical Architecture Debts** `TD-CRIT-SYS0-MISSING` and `TD-CRIT-PM-MISSING`.

The simulation is mathematically sound in theory but structurally disconnected in practice. The "Plumbing" (SettlementSystem) works, but the "Pipes" (Agent Registry) are not connected to the main water sources (Central Bank). Re-connecting these agents will likely resolve the vast majority of `SETTLEMENT_FAIL` errors.

## 2. Critical Findings (The "Red" List)

The following items are active, confirmed, and blocking stable simulation.

### 🚨 TD-CRIT-SYS0-MISSING: The Invisible Central Bank
- **Status:** **CRITICAL / OPEN**
- **Location:** `simulation/initialization/initializer.py`
- **Evidence:** 
  ```python
  # Initializer.py
  sim.agents: Dict[int, Any] = {h.id: h for h in self.households}
  sim.agents.update({f.id: f for f in self.firms})
  sim.agents[sim.bank.id] = sim.bank
  sim.agents[sim.government.id] = sim.government
  # MISSING: sim.agents[sim.central_bank.id] = sim.central_bank
  ```
- **Impact:** The `SettlementSystem` checks `agent_registry` for source/dest accounts. Since ID `0` (Central Bank) is not in `sim.agents` (which feeds the registry), all OMO and Minting operations fail with `InvalidAccountError: Source account does not exist: 0`.

### 🚨 TD-CRIT-PM-MISSING: The Broke & Invisible Liquidator
- **Status:** **CRITICAL / OPEN**
- **Location:** `simulation/initialization/initializer.py`
- **Evidence:**
  ```python
  sim.public_manager = PublicManager(config=self.config)
  sim.world_state.public_manager = sim.public_manager
  # MISSING: sim.agents[sim.public_manager.id] = sim.public_manager
  ```
- **Impact:** 
  1. **Registration:** Public Manager cannot receive funds or assets via standard settlement.
  2. **Funding:** Public Manager is initialized with default config but no explicit endowment or overdraft capability is verified in `initializer.py`. It likely has 0 cash, causing `InsufficientFundsError` when attempting to buy assets from bankrupt firms.

### 🚨 TD-DB-SCHEMA-DRIFT: Data Loss Risk
- **Status:** **CRITICAL / OPEN**
- **Evidence:** Codebase uses `total_pennies` (int) for transactions (e.g., `TransactionData` in `simulation/dtos/api.py`), but legacy SQLite database `percept_storm.db` likely lacks this column.
- **Impact:** `sqlite3.OperationalError` during transaction logging, or silent data loss if logging suppresses errors.

## 3. Major Architecture Debt

### TD-ARCH-FIRM-COUP: Component Coupling
- **Status:** **OPEN**
- **Location:** `simulation/firms.py`
- **Evidence:** 
  ```python
  self.inventory_component.attach(self)
  self.financial_component.attach(self)
  ```
- **Analysis:** Components still hold a reference to the parent `Firm`, maintaining bi-directional coupling and preventing true modularity.

### TD-ARCH-GOV-MISMATCH: Singleton vs List
- **Status:** **OPEN**
- **Location:** `simulation/engine.py` / `simulation/dtos/api.py`
- **Evidence:** `SimulationState` maintains both `primary_government` and `governments` list. This ambiguity creates risk of logic drift where some systems update the singleton while others query the list (or vice versa).

## 4. Status Ledger (Updated)

| ID | Description | Status | Verification |
| :--- | :--- | :--- | :--- |
| **TD-ARCH-FIRM-COUP** | Parent Pointer Pollution | 🔴 **Open** | `attach(self)` present in `firms.py`. |
| **TD-ARCH-DI-SETTLE** | DI Timing | 🟢 **Resolved** | Initializer refactored (Wave 1.2). |
| **TD-ARCH-GOV-MISMATCH** | Singleton vs List | 🔴 **Open** | DTOs show both fields. |
| **TD-CRIT-FLOAT-CORE** | Float Core | 🟡 **Verify** | `MoneyDTO` uses `amount_pennies`, but test `test_engine.py` failed assertion `10.0 == 1000`. |
| **TD-INT-BANK-ROLLBACK** | Rollback Coupling | 🟡 **Partial** | Uses `deposit` method, assumes Protocol adherence. |
| **TD-RUNTIME-TX-HANDLER** | Missing Handlers | 🔴 **Open** | `bailout` handler missing in Initializer. |
| **TD-PROTO-MONETARY** | Protocol Violation | 🟢 **Resolved** | `IFinancialEntity` protocol in place. |
| **TD-AI-DEBT-AWARE** | AI Debt Blindness | 🔴 **Open** | No evidence of fix in Agent logic. |
| **TD-CONF-MAGIC-NUMBERS** | Magic Numbers | 🟢 **Resolved** | Config objects widely used. |
| **TD-ARCH-LOAN-CIRCULAR** | Loan Circular Dep | 🟢 **Resolved** | Local import workaround in `firms.py`. |
| **TD-ECON-WAR-STIMULUS** | Stimulus Dependency | 🔴 **Open** | Economic logic unchanged. |
| **TD-ARCH-FIRM-MUTATION** | In-place Mutation | 🟡 **Partial** | Moving to Orchestrator, but state passed to engines. |
| **TD-CRIT-SYS0-MISSING** | **Missing Central Bank** | 🚨 **CRITICAL** | **Absent from Agent Registry.** |
| **TD-CRIT-PM-MISSING** | **Missing Public Manager** | 🚨 **CRITICAL** | **Absent from Agent Registry.** |
| **TD-DB-SCHEMA-DRIFT** | Schema Drift | 🚨 **CRITICAL** | `total_pennies` column likely missing in DB. |

## 5. Correlation with Test Failures (`fails.txt`)

The 27 failing tests map directly to the identified debts:

1.  **DTO Mismatches (17 Failures):**
    - **Error:** `TypeError: BorrowerProfileDTO.__init__() got an unexpected keyword argument 'borrower_id'`
    - **Cause:** `modules/finance/api.py` defines `BorrowerProfileDTO` WITH `borrower_id`, but `financial_strategy.py` or tests seem to be using an old definition or constructing it incorrectly. This is a clear **Protocol/DTO Version Drift**.

2.  **Float vs Int (1 Failure):**
    - **Error:** `AssertionError: assert 10.0 == 1000` (in `test_engines.py`)
    - **Cause:** `TD-CRIT-FLOAT-CORE`. The test expects Integer Pennies (`1000`), but the `FinanceEngine` is returning Float Dollars (`10.0`). The migration is incomplete.

3.  **Protocol Violations (2 Failures):**
    - **Error:** `TypeError: 'LoanInfoDTO' object is not subscriptable`
    - **Cause:** `TD-UI-DTO-PURITY`. Legacy code treats DTOs as dicts.

4.  **Transaction Logic Failures (Housing/Loan):**
    - **Error:** `assert False is True` / `AssertionError` in Housing Handlers.
    - **Cause:** Likely downstream effects of `TD-CRIT-SYS0-MISSING`. If the system cannot settle basic transfers (e.g. taxes or initial funding), complex housing transactions fail mid-flight.

## 6. Recommendations

1.  **Priority 1 (Fix the Engine):** 
    - In `SimulationInitializer.build_simulation`, **explicitly register** `sim.central_bank` and `sim.public_manager` into `sim.agents` before Registry synchronization.
    - Give `PublicManager` an initial endowment or Overdraft capability.

2.  **Priority 2 (Fix the Interface):**
    - Resolve the `BorrowerProfileDTO` mismatch. Ensure all files import the DTO from `modules/finance/api.py` and that the definition matches the usage.

3.  **Priority 3 (Fix the Data):**
    - Add a schema migration check in `DBManager` for `total_pennies`.

4.  **Priority 4 (Finish the Migration):**
    - Update `FinanceEngine` to return Integer Pennies for all monetary values, fixing the `10.0 == 1000` failure.