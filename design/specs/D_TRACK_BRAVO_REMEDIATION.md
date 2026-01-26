```markdown
# Remediation Spec: Track Bravo - Policy Purity & Interfaces

**Objective:** This document outlines the technical specification to resolve critical technical debts TD-110 and TD-119. The focus is on enforcing architectural purity by ensuring atomic settlements and formalizing key financial interfaces.

**Related WO:** `WO-120` (tentative)
**Priority:** CRITICAL
**Author:** Gemini (Administrative Assistant)

---

## 1. TD-110: Phantom Tax Revenue

### 1.1. Problem Statement
The current system suffers from "phantom revenue," where tax income is recorded without a verified, successful fund transfer. This violates the `Settle -> Record` architectural pattern and compromises the integrity of the government's budget and all dependent economic analytics. The root cause is a leaky abstraction where state recording is not strictly decoupled from the settlement attempt.

### 1.2. Remediation Plan: Enforce the `Settle -> Record` Pattern

The remediation will enforce a strict one-way data flow. `TaxAgency` is responsible for *attempting* collection. `Government` is responsible for *recording* the verified outcome.

#### 1.2.1. Step 1: Solidify `TaxAgency` as an Atomic Collector

The `TaxAgency.collect_tax` method is the **sole authorized entry point** for any tax collection. Its responsibilities are strictly limited to:
1.  Receiving payer, payee, and amount.
2.  Interacting with the injected `ISettlementSystem` to perform an atomic fund transfer.
3.  Returning a `TaxCollectionResult` DTO that immutably describes the transaction's outcome (`success` flag and `amount_collected`).

**No changes are required in `simulation/systems/tax_agency.py`**, as its current implementation already adheres to this principle. The focus is on its usage.

#### 1.2.2. Step 2: Solidify `Government` as a Responsible Recorder

The `Government.record_revenue` method is the **sole authorized entry point** for updating the government's internal financial ledgers (e.g., `total_collected_tax`, `revenue_this_tick`).

This method MUST only be called *after* receiving a **successful** `TaxCollectionResult` DTO from `TaxAgency.collect_tax`.

**Code Review Mandate:** All call sites for tax collection within `government.py` must be audited to ensure they follow this exact pattern:

```python
# CORRECT PATTERN TO BE ENFORCED
# Location: e.g., government.py -> run_welfare_check

# 1. Attempt settlement via TaxAgency
result = self.tax_agency.collect_tax(
    payer=agent,
    payee=self,
    amount=tax_amount,
    tax_type="wealth_tax",
    settlement_system=self.settlement_system,
    current_tick=current_tick
)

# 2. Conditionally record the verified outcome
if result['success']:
    self.record_revenue(result)
```

#### 1.2.3. Step 3: Deprecate and Remove Legacy Pathways

The legacy adapter `Government.collect_tax` is a major risk. While immediate removal might break the `TransactionProcessor`, it must be phased out.

1.  **Mark for Deprecation:** Add a prominent `DeprecationWarning` to `Government.collect_tax`, pointing to the new standard of direct `tax_agency.collect_tax` calls followed by `record_revenue`.
2.  **Audit `TransactionProcessor` (Future Work):** A new technical debt task (TD-120) must be created to audit `TransactionProcessor` and refactor its calls away from `Government.collect_tax`.

### 1.3. Verification Plan
1.  **Static Analysis:** Use `search_file_content` to find all usages of `total_collected_tax` and `revenue_this_tick` within `government.py`. Any modification to these attributes outside of `record_revenue` is a failure.
2.  **Unit Testing:** Write a unit test for `Government` that mocks `tax_agency.collect_tax` to return both successful and failed `TaxCollectionResult` DTOs.
    - Assert that `record_revenue` is **only** called when the result is successful.
    - Assert that the government's assets and tax ledgers remain unchanged when the result is a failure.

---

## 2. TD-119: Formalize `IBankService` Protocol

### 2.1. Problem Statement
The `IBankService` protocol is implicitly defined but not formally implemented by the `Bank` class. Furthermore, the protocol definition in `modules/finance/api.py` is mismatched with the `Bank` class's actual implementation, specifically regarding the `add_bond_to_portfolio` method. This creates interface inconsistency and risk of static analysis or runtime errors.

### 2.2. Remediation Plan: Align Protocol with Reality

The remediation will align the `IBankService` protocol with the existing, stable implementation of the `Bank` class. Introducing new, unimplemented features to the `Bank` is out of scope for this fix.

#### 2.2.1. Step 1: Refine `IBankService` Protocol

The `add_bond_to_portfolio` method is not a core function of the current `Bank` implementation. It will be removed from the protocol to reflect the implemented reality.

**File:** `modules/finance/api.py`
**Change:** Remove the `add_bond_to_portfolio` method from the `IBankService` protocol.

```python
# modules/finance/api.py

class IBankService(IFinancialEntity, Protocol):
    """Interface for commercial and central banks."""
    # The following method will be removed as it's not a core function
    # of the current Bank implementation.
    # def add_bond_to_portfolio(self, bond: BondDTO) -> None: ...
    pass # The protocol now correctly reflects the Bank's capabilities
```

#### 2.2.2. Step 2: Explicitly Implement the Protocol

The `Bank` class will be explicitly declared as an implementer of the now-matching `IBankService` protocol. This makes the relationship clear and allows for robust type checking.

**File:** `simulation/bank.py`
**Change:** Update the `Bank` class signature to inherit from `IBankService`.

```python
# simulation/bank.py

# ... imports
from modules.finance.api import InsufficientFundsError, IBankService # IBankService is imported
# ...

# Change class signature from IFinancialEntity to IBankService
class Bank(IBankService):
    """
    Phase 3: Central & Commercial Bank Hybrid System.
    WO-109: Refactored for Sacred Sequence (Transactions).
    """

    def __init__(self, id: int, initial_assets: float, config_manager: ConfigManager, settlement_system: Optional["ISettlementSystem"] = None):
        # ... no other changes needed in __init__
```

### 2.3. Verification Plan
1.  **Static Analysis (`mypy`):** After the changes, run `mypy` on the `simulation/` and `modules/` directories. The check must pass without errors, confirming that `Bank` correctly implements the `IBankService` protocol.
2.  **Code Review:** Confirm that the `add_bond_to_portfolio` method has been removed from `IBankService` and that the `Bank` class signature has been updated.

---

## 3. 🚨 Risk & Impact Audit (Summary)

-   **TD-110 (Phantom Tax):** The primary risk remains the legacy `TransactionProcessor`. The changes specified here are safe and correct, but the phantom revenue issue may persist until the `TransactionProcessor` is refactored. Modifying the `Government` God Class is inherently risky; changes must be limited to the scope defined above.
-   **TD-119 (IBankService):** Risk is low. This change aligns the interface with the implementation, improving code quality and maintainability without altering runtime logic.

## 4. 📝 Mandatory Reporting (Jules's Task)

Upon implementing these changes, the developer (Jules) is required to:
1.  **Document Discoveries:** If any other modules are found to be calling `Government.collect_tax` or modifying government revenue ledgers directly, they must be documented in `communications/insights/YYYY-MM-DD_tax_remediation_findings.md`.
2.  **Update Tech Debt:** Create a new entry `TD-120: Refactor TransactionProcessor Tax Calls` in `design/TECH_DEBT_LEDGER.md`.
```
