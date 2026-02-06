# Mission Guide: Structural Debt Clearance (Track 3)

## 1. Objectives
- **TD-254**: Resolve `hasattr` abstraction leaks in `SettlementSystem`. Transition to strict interface/protocol-based checks.
- **TD-035**: Generalize hardcoded Political AI heuristics in `AdaptiveGovPolicy`.
- **TD-188**: Fix documentation drift related to config paths in `PROJECT_STATUS.md` and related docs.

## 2. Reference Context (MUST READ)
- **Primary Files**:
  - `simulation/systems/settlement_system.py`: Focus on `_execute_withdrawal` and `execute_settlement` where `hasattr` is used.
  - `simulation/policies/adaptive_gov_policy.py`: Refactor `_execute_action` to use configuration-driven deltas.
- **Metadata**:
  - `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`: TD definitions.
  - `design/1_governance/architecture/ARCH_TRANSACTIONS.md`: Zero-sum principles.

## 3. Implementation Roadmap

### Phase 1: Settlement Hardening (TD-254)
1.  Identify all instances of `hasattr(agent, 'id')`, `hasattr(agent, 'agent_type')`, etc. in `settlement_system.py`.
2.  Ensure agents passed to `SettlementSystem` strictly adhere to `IFinancialEntity` or relevant protocols (e.g., `IPortfolioHandler`).
3.  Replace `hasattr` checks with proper interface methods or identified attribute access if the protocol is guaranteed.

### Phase 2: Political AI Generalization (TD-035)
1.  Extract hardcoded magic numbers (0.1, 2.0, 0.05, 0.6) from `AdaptiveGovPolicy._execute_action`.
2.  Move these to `economy_params.yaml` or the relevant config DTO.
3.  Update the policy to read these bounds from the config.

### Phase 3: Documentation Sync (TD-188)
1.  Audit `PROJECT_STATUS.md` for stale configuration paths.
2.  Synchronize documentation with the actual file structure (e.g., ensure links to `economy_params.yaml` are correct).

## 4. Verification
- `pytest tests/unit/test_settlement_system.py`
- `python scripts/trace_leak.py` (Must stay at 0.0000%)
- Verify `AdaptiveGovPolicy` still functions correctly with extracted parameters.
