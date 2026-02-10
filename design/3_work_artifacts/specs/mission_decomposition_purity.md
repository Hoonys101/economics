# Mission: Decomposition Sprint (Total Engine Purity)

## Context
Recent audits identified "Abstraction Leaks" where raw agent handles (Firm, Government) and system handles (Wallet, IInventoryHandler) are passed to simulation engines. This violates the "Stateless Engine" pattern and creates fragile coupling.

## Objective
Refactor all simulation engines to communicate exclusively via DTOs (Data Transfer Objects). Engines should receive pure data and return result DTOs, leaving state mutation and orchestration to the Agent (Orchestrator).

## Phase 1: Firm Engine Purity
- [x] **ProductionEngine**: (Already completed by Antigravity)
- [ ] **HREngine**: 
    - Refactor `process_payroll` to accept `HRPayrollContextDTO` instead of `IWallet` and `Government`.
    - Gather tax rates/survival cost into the DTO.
    - Path: `simulation/components/engines/hr_engine.py`
- [ ] **SalesEngine**:
    - Refactor `generate_marketing_transaction` and `post_ask` to use DTOs only.
    - Path: `simulation/components/engines/sales_engine.py`

## Phase 2: Agent Orchestration Alignment
- [ ] **Firm Agent**:
    - Update `generate_transactions()` and `produce()` to gather necessary data into DTOs before calling engines.
    - Path: `simulation/firms.py`

## Phase 3: God Class Thinning (Initial)
- [ ] Group related logic into private helper methods in `Firm` to prepare for further extraction.
- [ ] Goal: Reduce `firms.py` line count.

## Verification
- Ensure all unit tests in `tests/unit/systems/` pass.
- Verify 0.00% M2 leak using `audit_economic_integrity.py`.
