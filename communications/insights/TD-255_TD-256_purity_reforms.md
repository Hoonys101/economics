# Technical Insight Report: Purity Reforms (TD-255 & TD-256)

## 1. Problem Phenomenon
*   **Direct State Access**: The codebase was rife with direct access to `agent.inventory`, treating it as a raw dictionary. This bypassed business rules (e.g., quality tracking) and made it impossible to enforce transactional integrity or logging.
*   **Saga Impurity**: `HousingTransactionSagaHandler` was accessing live agent objects (`simulation.agents.get(id)`) during saga execution steps (e.g., `_handle_initiated`), violating the principle of isolation for long-running transactions.
*   **DTO Mismatch**: A critical disconnect was identified between `HousingSystem` (producing `HousingPurchaseSagaDTO`) and `SagaHandler` (consuming `HousingTransactionSagaStateDTO`). The system relied on implicit compatibility or legacy fields (`buyer_id`) rather than strict typing.

## 2. Root Cause Analysis
*   **Legacy Architecture**: `BaseAgent` exposed `self.inventory` as a public dictionary, and early systems (`Registry`, `GoodsHandler`) were built to manipulate it directly.
*   **Module Drift**: The housing domain (`modules.housing`) and finance domain (`modules.finance`) evolved separate DTO definitions for similar concepts, leading to the mismatch in Saga structures.
*   **Lazy Loading Pattern**: The Saga Handler was designed to "resolve" agents at runtime rather than carrying a snapshot, likely to ensure data freshness, but this compromised the "Frozen State" requirement for robust sagas.

## 3. Solution Implementation Details
*   **Protocol Enforced Inventory**:
    *   Defined `IInventoryHandler` in `modules/simulation/api.py`.
    *   Refactored `Firm` and `Household` (via `BaseAgent`) to implement this protocol.
    *   Renamed `self.inventory` to `self._inventory` to discourage direct access.
    *   **Mitigation:** Added a backward-compatible `inventory` property to `BaseAgent` that aliases `_inventory`. This prevents immediate crashes in legacy systems (like `ma_manager`, `bootstrapper`) that still rely on direct attribute access, while marking the property as deprecated.
    *   Updated `GoodsTransactionHandler` and `Registry` to use `add_item`/`remove_item` methods.
*   **Snapshot Integration**:
    *   Defined `HouseholdSnapshotDTO` in `modules/simulation/api.py`.
    *   Updated `HousingSystem` to capture this snapshot at the moment of saga submission.
    *   Updated `HousingTransactionSagaHandler` to operate strictly on this snapshot (via `buyer_context`), removing all live agent lookups for financial data in the initiation phase.
*   **DTO Alignment**:
    *   Forced `HousingSystem` to construct the strict `HousingTransactionSagaStateDTO` (Finance version) instead of the loose `HousingPurchaseSagaDTO` to ensure compatibility with the Orchestrator and Handler.

## 4. Lessons Learned & Technical Debt Identified
*   **DTO Duplication**: `modules/housing/dtos.py` and `modules/finance/sagas/housing_api.py` contain overlapping definitions (`HousingTransactionSagaStateDTO`). This should be consolidated into a shared domain module.
*   **Registry Redundancy**: `simulation/systems/registry.py` contains logic (`_handle_goods_registry`) that duplicates `GoodsTransactionHandler`. The `Registry` class appears to be a legacy artifact that should be deprecated or merged.
*   **Inventory Access Violations**: The audit script (`scripts/audit_inventory_access.py`) revealed 60+ remaining violations in systems like `ma_manager.py`, `bootstrapper.py`, `persistence_manager.py`, and `liquidation_handlers.py`. These systems still access `.inventory` directly and need to be refactored to use `IInventoryHandler` or `Firm` specific methods.
*   **Quality Handling**: `IInventoryHandler` currently only supports `(item_id, quantity)`. Logic for `quality` updates is currently handled manually in `GoodsTransactionHandler` and `Registry` by checking for `inventory_quality` attributes. This should be incorporated into an extended protocol or the agent's internal logic.
