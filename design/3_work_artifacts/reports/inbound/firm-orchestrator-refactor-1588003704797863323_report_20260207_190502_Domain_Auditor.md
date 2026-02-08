# Domain Audit: Systems, Persistence & LifeCycles

### 🚥 Domain Grade: WARNING

### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `simulation/systems/analytics_system.py` | `43-85` | **Persistence Purity Violation**: The `AnalyticsSystem` directly accesses numerous internal agent properties (e.g., `agent.is_employed`, `agent.needs`, `agent.config`, `agent.current_production`) instead of using safe DTOs as specified in its own docstring (`L30-L31`). | Medium |
| `simulation/systems/ma_manager.py` | `160-192` | **Logic Duplication / Race Condition**: The `_execute_bankruptcy` method duplicates firm liquidation logic. This responsibility is now managed by `LifecycleManager` -> `LiquidationManager`, creating a high risk of processing bankruptcies twice or in conflicting ways. | High |
| `simulation/systems/analytics_system.py` | `156-159` | **Persistence Purity Violation**: Aggregation logic for `total_labor_income` and `total_capital_income` directly accesses `labor_income_this_tick` and `capital_income_this_tick` on household agents, breaking encapsulation. | Medium |

### 💡 Abstracted Feedback (For Management)
*   **Critical Logic Duplication**: There are two separate and conflicting systems for handling firm bankruptcy (`MAManager` and `LifecycleManager`). This is a major structural issue that can lead to incorrect state, data corruption, and unpredictable simulation outcomes. The legacy `MAManager` logic should be deprecated and removed.
*   **Persistence Layer Drift**: The data aggregation system (`AnalyticsSystem`) has drifted from its design principles. It directly accesses live agent state instead of using designated safe interfaces (DTOs), breaking encapsulation and creating a risk of inconsistent data reads during persistence.
*   **Orchestration Unverified**: The core simulation loop (`tick_orchestrator.py`) was not provided, so its adherence to the master architectural document (`ARCH_SEQUENCING.md`) could not be audited. This is a significant gap in the audit.