# Structural Audit Report

## 1. God Class Detection
The following files contain classes that exceed the 800-line threshold, indicating potential "God Class" anti-patterns where a single class manages too many responsibilities.

| File Path | Line Count | Primary Class |
|-----------|------------|---------------|
| `simulation/firms.py` | 1386 | `Firm` |
| `simulation/core_agents.py` | 1045 | `Household` |
| `config/__init__.py` | 945 | N/A (Module) |
| `tests/system/test_engine.py` | 840 | `TestEngine` |
| `simulation/systems/settlement_system.py` | 813 | `SettlementSystem` |

**Recommendation:**
- Refactor `Firm` and `Household` by extracting more behaviors into stateless engines or components.
- Break down `SettlementSystem` into smaller specialized services (e.g., `TransferService`, `EscrowService`).
- Split `config/__init__.py` into sub-modules.

## 2. Abstraction Leak Analysis
This section details instances where "Raw Agents" (Concrete `Firm` or `Household` classes) are leaked into Service Interfaces or Decision Engines, bypassing DTOs or Protocols.

### Leaks in Service Interfaces
| Module | Interface | Method | Leak Description |
|--------|-----------|--------|------------------|
| `modules/hr/api.py` | `IHRService` | `calculate_liquidation_employee_claims` | Accepts concrete `Firm` instead of `IFirm` or a specific State DTO. |
| `modules/finance/api.py` | `ITaxService` | `calculate_liquidation_tax_claims` | Accepts concrete `Firm` instead of `IFirm` or a specific State DTO. |
| `modules/finance/api.py` | `IFinanceSystem` | `evaluate_solvency` | Accepts concrete `Firm` (via forward ref) instead of `IFirm`. |
| `modules/finance/api.py` | `IFinanceSystem` | `request_bailout_loan` | Accepts concrete `Firm` (via forward ref) instead of `IFirm`. |

### Leaks in Decision Engines
No direct leaks were found in the core logic of scanned engines (`BrandEngine`, `HREngine`, `FiscalEngine`, `MonetaryEngine`, `ConsumptionManager`). They correctly utilize State DTOs (`SalesState`, `HRState`, etc.) or specific contexts (`DecisionContext`).

However, the `Firm` class (Orchestrator) invokes engines by passing internal state objects which are tightly coupled to the Agent's structure. While better than passing `self`, the `IHRService` and `ITaxService` interfaces (used within `LiquidationContext`) force the dependency on the concrete `Firm` class back into the system.

**Recommendation:**
- Replace concrete `Firm` type hints in `modules/hr/api.py` and `modules/finance/api.py` with `IFirm` protocol or specific DTOs (e.g., `ILiquidatableFirm`).
- Ensure `IFirm` protocol in `modules/simulation/api.py` exposes necessary attributes for these services.
