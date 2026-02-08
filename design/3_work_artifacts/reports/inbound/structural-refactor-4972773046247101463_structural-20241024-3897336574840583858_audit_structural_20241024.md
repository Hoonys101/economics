# Structural & Abstraction Audit Report

**Date:** 2024-10-24
**Auditor:** Jules
**Target:** `simulation/core_agents.py`, `simulation/firms.py`, `simulation/orchestration/tick_orchestrator.py`

## 1. Saturation Analysis (God Class Check)

| Class | File | Lines | Status |
| :--- | :--- | :--- | :--- |
| `Household` | `simulation/core_agents.py` | 470 | ✅ Decomposition Successful |
| `Firm` | `simulation/firms.py` | 435 | ✅ Decomposition Successful |
| `Bank` | `simulation/bank.py` | 707 | ⚠️ Approaching Saturation (800 limit) |
| `TickOrchestrator` | `simulation/orchestration/tick_orchestrator.py` | 250 | ✅ Safe |

**Findings:**
- `Household` and `Firm` have been successfully decomposed into components (`BioComponent`, `HRDepartment`, etc.).
- `Bank` is large (707 lines) and handles multiple responsibilities (deposits, loans, clearing). It is the primary candidate for future decomposition.

## 2. Abstraction Leak Analysis (Dependency Hell)

**Criteria:** Raw agent objects leaking into decision engines or tight coupling.

| Component | Location | Leak Description | Severity |
| :--- | :--- | :--- | :--- |
| `FinanceDepartment` | `process_profit_distribution` | Iterates over `households: List[Household]` (Raw Agents) to check `portfolio` for dividends. This is O(N*M) and exposes raw agents. | 🔴 Critical |
| `HRDepartment` | `self.employees` | Maintains `List[Household]` directly. Tightly couples Firm logic to Household instances. | 🔴 Critical |
| `Firm` | `generate_transactions` | Accepts `all_households` raw list and passes it to `FinanceDepartment`. | 🔴 Critical |
| `Household` | `make_decision` | Passes `input_dto.housing_system` (likely a service/system object) to `OrchestrationContextDTO`. | 🟡 Moderate |

**Findings:**
- **Dividend Logic Leak:** Firms iterating over all households to find shareholders is a significant performance bottleneck and abstraction leak. It should use a `StockMarket` or `ShareholderRegistry` service.
- **HR Coupling:** `HRDepartment` holding direct references to `Household` objects makes serialization and strict separation difficult.

## 3. Sequence Exception Analysis

**Criteria:** Bypassing `tick_orchestrator.py` phases or standard pipeline.

| Location | Issue | Recommendation |
| :--- | :--- | :--- |
| `TickOrchestrator.run_tick` | Inline Tick 0 Money Supply logic & Government flow reset. | Move to `Phase0_PreSequence` or specialized initialization phase. |
| `TickOrchestrator._finalize_tick` | Inline M2 Leak Calculation and logging. | Move to `Phase_MonetaryProcessing` or `EconomicIndicatorTracker`. |

**Findings:**
- `TickOrchestrator` is relatively clean but contains "Analysis" logic (`_finalize_tick`) that mixes orchestration with business logic (M2 calculation).

## 4. Recommendations for Next Steps

1.  **Decompose `Bank` Class:** Proactive refactoring before it exceeds 800 lines.
2.  **Fix Dividend Leak:** Implement `ShareholderRegistry` to allow Firms to look up their shareholders without iterating all households.
3.  **Refactor HR/Finance Interfaces:** Replace `List[Household]` with `List[int]` (IDs) and use a localized `IAgentService` or DTOs for necessary data interactions.
4.  **Clean up Orchestrator:** Move M2 verification and Tick 0 setup into appropriate Phases.