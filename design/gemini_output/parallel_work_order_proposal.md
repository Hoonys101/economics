# 🚀 Parallel Work Order Proposal: Scalable Remediation

Based on the [TECH_DEBT_LEDGER.md](file:///c:/coding/economics/design/TECH_DEBT_LEDGER.md), we have organized the remaining high-priority tasks into independent tracks. These tracks target non-overlapping files, allowing multiple **Jules** agents (or sequential sessions) to proceed without merge conflicts.

---

## 🏗️ Track Alpha: Monetary Initialization & Leak Hunt
**Focus**: Initialization integrity and M2 money supply accounting.
- **TD-115**: Root cause capture of the -99,680 asset leak at Tick 1.
- **TD-111**: Exclude `RefluxSystem` balance from M2 calculation.

| Module | Target File | Conflict Status |
|---|---|---|
| **Initializer** | `simulation/initialization/initializer.py` | ✅ Pure |
| **Reflux** | `simulation/systems/reflux_system.py` | ✅ Pure |
| **Integrity** | `simulation/world_state.py` | ⚠️ Shared |

---

## 🏛️ Track Bravo: Policy Purity & Interface Ghosting
**Focus**: Government accounting accuracy and interface formalization.
- **TD-110**: Phantom Tax Revenue fix (decoupling stats from transfer).
- **TD-119**: Formal definition of `IBankService` Protocol.

| Module | Target File | Conflict Status |
|---|---|---|
| **Tax** | `simulation/systems/tax_agency.py` | ✅ Pure |
| **Government** | `simulation/agents/government.py` | ✅ Pure |
| **Finance API** | `modules/finance/api.py` | ✅ Pure |

---

## 🧪 Track Charlie: Quality Guard (Post-Core)
**Focus**: Removing legacy fallbacks and expanding coverage.
- **TD-113**: Removal of legacy `withdraw/deposit` fallbacks.
- **TD-114**: Implementation of sparse system tests (Housing, Education).

| Module | Target File | Conflict Status |
|---|---|---|
| **Processor** | `simulation/systems/transaction_processor.py` | 🛑 Blocked by Core |
| **Tests** | `tests/system/` | ✅ Pure (New Files) |

---

## 📈 Summary for PM
- **Immediately Dispatchable**: Track Alpha & Track Bravo.
- **Dependency**: Track Charlie requires completion of the current `Remediation_TD116_117_118` mission.

> [!TIP]
> Use `scripts/cmd_ops.py` to prepare the specs for Alpha and Bravo tracks in parallel while the current mission is running.
