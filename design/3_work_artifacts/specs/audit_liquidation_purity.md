# Audit: TD-LIQ-INV Protocol Purity for Liquidation Handlers

## 1. Problem Statement
The `InventoryLiquidationHandler` currently violates architectural boundaries by using Python's dynamic `getattr` and `hasattr` to access internal attributes of agents, specifically `config.fire_sale_discount` and `config.goods`. 

This creates implicit coupling to the concrete `Firm` class structure. If `Firm.config` structure changes (e.g., renaming `fire_sale_discount`), the liquidation system will silently fail or require lock-step updates.

**Current Violation:**
```python
# Anti-pattern in InventoryLiquidationHandler
haircut = getattr(agent.config, "fire_sale_discount", 0.2) 
initial_prices = getattr(agent.config, "goods", {})
```

## 2. Target Architecture (Protocol Purity)
We must replace implicit attribute access with explicit Protocol definitions and Data Transfer Objects (DTOs).

### 2.1. New DTO: `LiquidationConfigDTO`
Create this in `modules/simulation/api.py` or `simulation/dtos/liquidation_dtos.py` (if new file needed).

```python
@dataclass
class LiquidationConfigDTO:
    haircut: float
    initial_prices: Dict[str, float]
    default_price: float
    market_prices: Dict[str, float]  # For mark-to-market
```

### 2.2. New Protocol: `IConfigurable`
Define this in `modules/simulation/api.py`.

```python
@runtime_checkable
class IConfigurable(Protocol):
    def get_liquidation_config(self) -> LiquidationConfigDTO:
        ...
```

### 2.3. Agent Implementation
The `Firm` class (and any other liquidatable agent) must implement this protocol using the `IConfigurable` interface. The implementation should map internal state to the DTO.

```python
# In Firm.py
class Firm(..., IConfigurable):
    def get_liquidation_config(self) -> LiquidationConfigDTO:
        # Map internal config to DTO
        return LiquidationConfigDTO(...)
```

### 2.4. Handler Refactor
Refactor `InventoryLiquidationHandler.py` to uses the protocol.

```python
if isinstance(agent, IConfigurable):
    config = agent.get_liquidation_config()
    haircut = config.haircut
    ...
```

## 3. Testing Requirements
- **Mock Specs**: Tests must use `spec=IConfigurable` or `spec=Firm` when mocking agents in liquidation tests.
- **Verification**: Ensure no `getattr` calls remain in the handler for these attributes.

## 4. Execution Plan
1.  Define DTO and Protocol in `modules/simulation/api.py` (or appropriate API module).
2.  Implement `get_liquidation_config` in `Firm.py`.
3.  Refactor `InventoryLiquidationHandler` to use the new method.
4.  Run `pytest tests/unit/test_liquidation.py` (or valid path) to verify.
