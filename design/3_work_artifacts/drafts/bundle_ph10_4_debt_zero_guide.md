# Mission Guide: Phase 10.4 Debt Zero (Protocol Purification)

## 1. Objectives
- **[TD-LIQ-INV]**: Replace `getattr(agent, 'config')` in `InventoryLiquidationHandler` with a formal `IConfigurable` protocol.

## 2. Core Components
- **API Definition**: [modules/simulation/api.py](file:///c:/coding/economics/modules/simulation/api.py)
- **Handler Implementation**: [simulation/systems/liquidation_handlers.py](file:///c:/coding/economics/simulation/systems/liquidation_handlers.py)
- **Technical Specification**: [draft_132559_Generate_a_Technical_Specifica.md](file:///c:/coding/economics/design/3_work_artifacts/drafts/draft_132559_Generate_a_Technical_Specifica.md)

## 3. Implementation Roadmap
1.  **Define `LiquidationConfigDTO` & `IConfigurable`** in `modules/simulation/api.py`.
2.  **Implement `IConfigurable` in `Firm`** (and any other liquidatable agents).
    - `get_liquidation_config()` should extract `haircut` and `initial_prices` from the internal config object.
3.  **Refactor `InventoryLiquidationHandler.liquidate()`**:
    - Remove all `getattr` and `hasattr` calls.
    - Use `liq_config = agent.get_liquidation_config()` via the protocol.
4.  **Update Unit Tests**:
    - Update mocks to implement `get_liquidation_config()` instead of just having a `.config` attribute.

## 4. Verification
- [ ] `pytest tests/unit/test_liquidation_manager.py` (and related handler tests).
- [ ] No `getattr` related to config remains in `liquidation_handlers.py`.
