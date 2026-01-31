# Work Order: - Sovereign Debt & Corporate Finance Implementation

**Phase:** Phase 26.5
**Priority:** HIGH
**Prerequisite:** (Settlement System)

## 1. Problem Statement
The current simulation lacks the mechanisms to handle government deficits and effectively tax corporations in an atomic manner. Direct asset modifications have been banned, necessitating a new implementation using the `SettlementSystem`.

## 2. Objective
Implement the sovereign debt market (Bond issuance) and corporate tax collection pipelines using the new atomic `SettlementSystem`.

## 3. Implementation Plan

### Track A: Fiscal Infrastructure (`modules/finance/`)
1. **Protocol Definition**: Update `modules/finance/api.py` to formalize `IFinancialEntity`, `IBankService`, `IFinanceSystem`, and `IFiscalMonitor` Protocols.
2. **FiscalMonitor**: Create `modules/analysis/fiscal_monitor.py` to calculate Debt-to-GDP and fiscal health metrics statelessly.
3. **FinanceSystem Upgrade**:
 - Implement `issue_treasury_bonds` using `settlement_system.transfer`.
 - Implement `collect_corporate_tax` using `settlement_system.transfer`.
 - Refactor `service_debt` to use atomic transfers.

### Track B: Agent Integration (`simulation/agents/`)
1. **Government**: Refactor `Government` agent to remove direct asset logic.
 - Delegate deficit financing to `finance_system.issue_treasury_bonds`.
 - Delegate tax collection to `tax_agency -> finance_system`.
2. **TaxAgency**: Update `collect_tax` to call `finance_system.collect_corporate_tax` instead of modifying assets.

### Track C: Verification
1. **Unit Tests**: Create `tests/modules/finance/test_sovereign_debt.py` covering bond issuance and tax collection atomicity.
2. **Integration**: Verify that `Bank` assets decrease and `Government` assets increase when bonds are issued.

## 4. Verification Criteria
- `FinanceSystem` methods must NEVER access `.assets` directly.
- `SettlementSystem.transfer` logs must show "Govt Bond Sale" and "Corporate Tax".
- Zero-sum property must hold true across all fiscal operations.

## 5. Jules Assignment
| Track | Task | Files |
|---|---|---|
| Track A | Core Finance Logic | `modules/finance/api.py`, `modules/finance/system.py`, `modules/analysis/fiscal_monitor.py` |
| Track B | Agent Refactoring | `simulation/agents/government.py`, `simulation/systems/tax_agency.py` |
| Track C | Testing | `tests/modules/finance/test_sovereign_debt.py` |

**Mandatory Reporting**: Log insights to `communications/insights/WO-113-sovereign-debt-insights.md`.
