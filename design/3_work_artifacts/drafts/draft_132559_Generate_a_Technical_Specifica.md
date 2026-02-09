# Technical Specification: TD-LIQ-INV Protocol Purity

## 1. Overview
This document outlines the technical plan to resolve technical debt item `TD-LIQ-INV`. The core issue is the use of `getattr(agent, 'config')` within `InventoryLiquidationHandler`, which violates protocol purity, is not type-safe, and creates a rigid dependency on an agent's internal structure.

The solution is to introduce a new `IConfigurable` protocol and a dedicated Data Transfer Object (DTO), `LiquidationConfigDTO`. This will decouple the handler from the concrete implementation of the agent, improve type safety, and make the agent's contract for providing configuration explicit.

## 2. API & DTO Definitions (`modules/simulation/api.py`)
To provide a clean and explicit contract, the following DTO and Protocol will be added to `modules/simulation/api.py`.

```python
# In modules/simulation/api.py

# ... existing code ...

# ===================================================================
# 6. Configuration & Parameterization Protocols (TD-LIQ-INV)
# ===================================================================

@dataclass(frozen=True)
class LiquidationConfigDTO:
    """
    Provides a flat, type-safe structure for liquidation-related configuration.
    This DTO is provided by an agent that implements the IConfigurable protocol.
    """
    haircut: float
    default_price: float
    initial_prices: Dict[str, float] # Maps item_id to its configured initial price

class IConfigurable(Protocol):
    """
    An interface for agents that can provide specific, structured configuration
    data to other systems, avoiding direct and unsafe attribute access.
    """
    def get_liquidation_config(self) -> LiquidationConfigDTO:
        """
        Constructs and returns a DTO containing all necessary parameters
        for the liquidation process.
        """
        ...

# ... existing code ...
```

## 3. Implementation Plan

### 3.1. `simulation.firms.Firm`
The `Firm` class, being the primary entity that can have its inventory liquidated, must implement the new `IConfigurable` protocol.

1.  **Implement `IConfigurable`**: The `Firm` class declaration will be updated to include `IConfigurable`.
2.  **Implement `get_liquidation_config` method**:
    *   This method will be responsible for reading the firm's internal `self.config` object.
    *   It will extract the `liquidation_haircut`, the default initial price, and the dictionary of all goods' initial prices.
    *   It will then instantiate and return a `LiquidationConfigDTO` with this data. This encapsulates the messy logic of accessing nested configuration attributes within the `Firm` class itself.

### 3.2. `simulation.systems.liquidation_handlers.InventoryLiquidationHandler`
The handler will be refactored to use the new protocol exclusively, removing all `getattr` calls related to configuration.

1.  **Type Check**: Before proceeding with liquidation, the handler will check if the agent `isinstance(agent, IConfigurable)`. If not, it cannot perform the operation and will return.
2.  **Fetch DTO**: It will call `agent.get_liquidation_config()` to retrieve the `LiquidationConfigDTO`.
3.  **Use DTO**: The handler will use the `haircut`, `default_price`, and `initial_prices` attributes from the DTO instead of accessing the raw config object. This makes the handler's dependency explicit and type-safe.

## 4. Pseudo-code (Refactoring `InventoryLiquidationHandler.liquidate`)

### Before
```python
# In InventoryLiquidationHandler.liquidate

# ...
firm = agent
default_price = 10.0
config = getattr(firm, "config", None)

if config and hasattr(config, "goods_initial_price") and isinstance(config.goods_initial_price, dict):
    default_price = config.goods_initial_price.get("default", 10.0)

haircut = getattr(config, "liquidation_haircut", 0.2) if config else 0.2
# ...
for item_id, qty in firm.get_all_items().items():
    # ...
    if price <= 0:
        if config and hasattr(config, "goods") and isinstance(config.goods, dict):
            price = config.goods.get(item_id, {}).get("initial_price", default_price)
        else:
            price = default_price
    # ...
```

### After
```python
# In InventoryLiquidationHandler.liquidate

# ...
# 1. Protocol Adherence Check
if not isinstance(agent, (IInventoryHandler, IConfigurable)):
    return

# 2. Fetch Structured Config via Protocol
try:
    liq_config = agent.get_liquidation_config()
except Exception: # Broad exception for safety if implementation is faulty
    logger.error(f"Agent {agent.id} failed to provide liquidation config.")
    return

haircut = liq_config.haircut
default_price = liq_config.default_price
# ...
firm = agent # Still need to treat as firm for inventory access
for item_id, qty in firm.get_all_items().items():
    # ...
    # 3. Use DTO for safe price fallback
    if price <= 0:
        price = liq_config.initial_prices.get(item_id, default_price)
    # ...
```

## 5. Verification Plan & Test Strategy
The introduction of the `IConfigurable` protocol necessitates an update to existing unit tests.

1.  **Identify Affected Tests**: All tests for `InventoryLiquidationHandler` and related liquidation logic must be reviewed.
2.  **Update Mocks**: Test mocks for agents (e.g., `Firm`) must be updated. Instead of attaching a mock `config` object directly (`mock_firm.config = ...`), the mocks must now implement the `get_liquidation_config` method.
3.  **Mock Implementation**: The mocked `get_liquidation_config` should be configured to return a `LiquidationConfigDTO` instance with appropriate values for each test case (e.g., different haircuts, different default prices).
    *   Example: `mock_firm.get_liquidation_config.return_value = LiquidationConfigDTO(haircut=0.5, default_price=15.0, initial_prices={'wood': 20.0})`
4.  **New Tests**: A new test should be added to verify that the handler correctly skips agents that do not implement the `IConfigurable` protocol.

## 6. Risk & Impact Audit

*   **Implicit Dependency on `Firm`**: This change *reduces* the implicit dependency. While `Firm` is the only implementer for now, the handler now depends on the abstract `IConfigurable` and `IInventoryHandler` protocols, not the concrete `Firm` class for its configuration needs.
*   **Nested Configuration Access**: This is fully resolved. The `LiquidationConfigDTO` flattens the required configuration, making access simple and safe for the handler. The complexity of navigating the raw config object is now correctly encapsulated within the `Firm` class.
*   **Protocol Definition Location**: The protocol and DTO will be correctly placed in `modules/simulation/api.py`, the central location for system-wide contracts, preventing circular dependencies.
*   **Test Impact**: High. As detailed in the verification plan, existing tests will break and require significant refactoring. This is a necessary cost for improving the architecture.
*   **Scope Creep**: The design strictly addresses the `config` access issue. The related problem of `getattr(firm, "last_prices")` is explicitly left out of scope and should be resolved separately, potentially with an `IValuationDataProvider` protocol. This design does not preclude that future work.

## 7. Mandatory Reporting Verification
All insights, architectural decisions, and potential future improvements discovered during the implementation of this specification will be documented in a new file under `communications/insights/TD-LIQ-INV_Protocol_Purity.md`. This ensures that the knowledge gained from this refactoring effort is captured and available for future reference.
