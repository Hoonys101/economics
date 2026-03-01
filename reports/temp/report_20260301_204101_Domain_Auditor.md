# ⚖️ Domain Auditor: Markets & Transaction Protocols

## 🚥 Domain Grade: ⚠️ WARNING

The market and transaction infrastructure demonstrates a strong commitment to Protocol-based design, but architectural "drift" in the form of monolithic DTOs and implicit registry lookups threatens the long-term isolation of market logic.

## ❌ Violations

| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `simulation/dtos/api.py` | L208-258 | **TD-ARCH-GOD-DTO**: `SimulationState` aggregates 40+ unrelated fields, forcing markets to depend on the entire engine. | High |
| `simulation/dtos/api.py` | L45-56 | **TD-FIN-FLOAT-RESIDUE**: `TransactionData` maintains `price: float` alongside `total_pennies: int`, creating risk of float incursion errors. | Medium |
| `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` | L32 | **TD-SYS-IMPLICIT-REGISTRY-LOOKUP**: `MonetaryLedger` uses `hasattr` chains to resolve registries instead of explicit Protocol injection. | Medium |
| `modules/system/api.py` | L126-130 | **Protocol Gap**: `IAgentBankruptcyEventDTO` uses raw `Dict[str, float]` for inventory without an enforced `IInventoryHandler`. | Low |

## 💡 Abstracted Feedback (For Management)

*   **Monolithic Dependency (The God DTO)**: The `SimulationState` DTO has evolved into a "God Class" for data. Markets should be refactored to consume scoped `IMarketContext` protocols to prevent unintended side-effects and improve testability.
*   **Precision Dualism**: The coexistence of `float` prices and `integer` pennies in transaction DTOs is a technical debt "time bomb." Complete migration to integer-only math is required to maintain zero-sum economic integrity.
*   **Weak Coupling via "Duck-Typing"**: Core systems are bypassing Protocol Purity by using `hasattr()` to find registries. This "Duck-Typed" resolution makes the market implementation fragile and difficult to refactor without breaking hidden dependencies.

## Conclusion
While the **Price Discovery** mechanisms (evidenced by `LaborMatchingResultDTO`) correctly stage changes as transactions, the **Registry Decoupling** and **DTO Consistency** metrics are trending downward due to structural bloat. Immediate focus should be on segregating the `SimulationState` and hardening the `IAgentRegistry` injection.