# ⚖️ Domain Auditor Report: Agents & Populations

### 🚥 Domain Grade: WARNING

### ❌ Violations

| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `design/1_governance/architecture/ARCH_AGENTS.md` | 53-81 | **Architectural Documentation Mismatch**: The document describes a "parent pointer" stateful component pattern for the `Firm` agent, but the implementation uses stateless engines that receive state DTOs. The documentation is incorrect. | High |
| `simulation/core_agents.py` | 600-614 | **SoC Violation**: `Household.add_item` directly mutates the internal state DTO (`_econ_state.inventory`), bypassing the component model. Inventory logic (like quality averaging) should be delegated, not implemented in the facade. | Medium |
| `simulation/core_agents.py` | 616-628 | **SoC Violation**: `Household.remove_item` directly mutates the internal state DTO (`_econ_state.inventory`). This duplicates the SoC violation from `add_item`. | Medium |
| `simulation/firms.py` | 483-490 | **Weak Encapsulation**: `Firm._add_inventory_internal` directly manipulates the `_inventory` dict. While part of the protocol implementation, this logic is in the facade rather than a dedicated inventory component, representing a minor architectural impurity. | Low |

### 💡 Abstracted Feedback (For Management)

*   **Architectural Documentation Drift**: The primary architecture document (`ARCH_AGENTS.md`) is dangerously out of sync with the `Firm` agent's implementation. It describes a stateful "parent-pointer" pattern that doesn't exist, while the code actually uses a cleaner, stateless engine pattern. This discrepancy poses a high risk of misleading future development.
*   **Protocol Purity Violation**: The `Household` agent breaks encapsulation by directly manipulating its internal state DTOs within its inventory management methods (`add_item`, `remove_item`). This violates the Separation of Concerns principle, as this logic should be handled by a dedicated component.
*   **Inconsistent State Patterns**: The `Firm` and `Household` agents, despite both being refactored, exhibit inconsistent state management patterns. `Household` correctly treats its state as immutable and receives new state objects from its components. In contrast, `Firm` passes mutable state objects to its engines to be modified directly, a less predictable and less robust pattern.
