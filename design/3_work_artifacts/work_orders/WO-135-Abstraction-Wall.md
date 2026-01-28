# Work Order: WO-135 - The Abstraction Wall

**Phase:** Refactoring
**Priority:** CRITICAL
**Prerequisite:** TD-103

## 1. Problem Statement

The "DTO Purity Gate" (TD-103) successfully decoupled decision engines from direct agent instances. However, a follow-up audit reveals significant architectural liabilities that undermine this abstraction:

1.  **Brittle Configuration Mapping**: `Household.make_decision` contains a large, manual block of code that maps ~50 attributes from a monolithic `config_module` to `HouseholdConfigDTO`. This is a major source of potential regressions, as any change in configuration requires manual updates, which are easily missed.
2.  **Incomplete Abstraction (Data Dictionaries)**: `DecisionContext` still passes `goods_data` and `market_data` as raw dictionaries (`Dict[str, Any]`). This allows unstructured data to penetrate the decision layer, violating the principle of a strictly-typed, DTO-only interface and hindering static analysis.
3.  **Single Responsibility Principle (SRP) Violation**: The `make_decision` methods in core agents are now responsible for both orchestrating decisions *and* acting as factories for complex configuration DTOs.

This work order mandates the construction of a true "Abstraction Wall" to resolve these issues, ensuring the decision-making process is pure, robust, and maintainable.

## 2. Objective

1.  **Automate Configuration DTO Creation**: Eliminate the manual mapping of `config_module` values by implementing a reusable, automated factory.
2.  **Enforce Absolute DTO Purity**: Replace all raw dictionary structures (`goods_data`, `market_data`) within `DecisionContext` with new, immutable, and strictly-typed DTOs.
3.  **Strengthen Verification**: Implement a robust testing strategy to prevent configuration drift and ensure data parity between the core simulation and the decision engines.
4.  **Restore SRP**: Refactor agent `make_decision` methods to delegate config DTO creation.

## 3. Proposed Architecture Changes

### 3.1. `ConfigFactory` for Automated DTO Population

A new utility will be introduced to handle the creation of configuration DTOs. This factory will use introspection to dynamically and safely populate a given config DTO from the main `config_module`.

**Location:** `simulation/utils/config_factory.py` (New file)

```python
# simulation/utils/config_factory.py
import dataclasses
from typing import Type, TypeVar

T = TypeVar('T')

def create_config_dto(config_module: object, dto_class: Type[T]) -> T:
    """
    Dynamically creates and populates a config DTO from a config module.
    It iterates over the DTO's fields and gets the corresponding (uppercase)
    attribute from the config module.
    """
    dto_fields = {f.name for f in dataclasses.fields(dto_class)}
    config_values = {}

    for field_name in dto_fields:
        config_key = field_name.upper()
        if hasattr(config_module, config_key):
            config_values[field_name] = getattr(config_module, config_key)
        else:
            # This provides a clear error when a config is missing
            raise AttributeError(
                f"Configuration Error: Attribute '{config_key}' not found in config_module "
                f"but is required by DTO '{dto_class.__name__}'."
            )
            
    return dto_class(**config_values)

```

This factory will be used within the agent `make_decision` method, replacing dozens of lines of manual mapping with a single, reliable call.

### 3.2. Strictly-Typed Data DTOs

To replace the raw dictionaries, the following `TypedDict`s will be added. `TypedDict` is chosen over `dataclass` for these specific cases as `goods_data` and `market_data` represent structured but essentially read-only collections of data from external sources (e.g., JSON files, simulation state), not objects with behavior.

**Location:** `simulation/dtos/api.py`

```python
# simulation/dtos/api.py
from typing import TypedDict, List, Dict

# For goods_data: List[Dict[str, Any]]
class GoodsDTO(TypedDict):
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: float
    base_need_satisfaction: float
    quality_modifier: float
    # ... any other fields from goods.json

# For market_data: Dict[str, Any] which holds market history
class MarketHistoryDTO(TypedDict):
    avg_price: float
    trade_volume: float
    # ... other historical market stats

# For market_snapshot DTO
class OrderDTO(TypedDict):
    agent_id: int
    item_id: str
    quantity: float
    price: float

class MarketSnapshotDTO(TypedDict):
    prices: Dict[str, float]
    volumes: Dict[str, float]
    asks: Dict[str, List[OrderDTO]]
    best_asks: Dict[str, float]

```

### 3.3. `DecisionContext` Finalization

The `DecisionContext` will be updated to use these new, strictly-typed DTOs.

**Location:** `simulation/dtos/api.py`

```python
# simulation/dtos/api.py
 @dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    """
    state: Union[HouseholdStateDTO, FirmStateDTO]
    config: Union[HouseholdConfigDTO, FirmConfigDTO]
    
    # --- Strictly-Typed Environmental Context ---
    goods_data: List[GoodsDTO] # REPLACES List[Dict]
    market_data: Dict[str, MarketHistoryDTO] # REPLACES Dict[str, Any]
    market_snapshot: MarketSnapshotDTO # Uses new OrderDTO

    # --- Other Context ---
    current_time: int
    government_policy: Optional[GovernmentPolicyDTO]
    stress_scenario_config: Optional[StressScenarioConfig] = None
```

### 3.4. Purity Gate Enhancement

The Purity Gate will be enhanced to check for the correct DTO types, ensuring no raw dictionaries slip through.

**Location:** `simulation/decisions/base_decision_engine.py`

```python
# simulation/decisions/base_decision_engine.py
class BaseDecisionEngine:
    def make_decisions(self, context: DecisionContext, ...):
        # 🚨 DTO PURITY GATE v2 🚨
        assert not hasattr(context, 'household') and not hasattr(context, 'firm')
        assert hasattr(context, 'state') and context.state is not None
        assert hasattr(context, 'config') and context.config is not None
        
        # NEW: Type-check for environmental data
        if context.goods_data:
            assert isinstance(context.goods_data[0], dict) # TypedDict is a dict at runtime
        if context.market_data:
            assert isinstance(next(iter(context.market_data.values())), dict)

        return self._make_decisions_internal(context, macro_context)
    # ...
```

## 4. Implementation Plan

### Track A: DTO Definition & Config Factory

1.  **Create `simulation/utils/config_factory.py`**: Implement the `create_config_dto` function as specified in section 3.1.
2.  **Create Unit Test for `ConfigFactory`**: In `tests/utils/test_config_factory.py`, create a test that uses a mock config object and a sample DTO to verify that the factory correctly populates the DTO and raises an `AttributeError` for missing configs.
3.  **Update `simulation/dtos/api.py`**:
    *   Add the `GoodsDTO`, `MarketHistoryDTO`, `OrderDTO`, and `MarketSnapshotDTO` TypedDicts.
    *   Update the `DecisionContext` dataclass to use these new types for `goods_data`, `market_data`, and `market_snapshot`.

### Track B: Agent & Engine Refactoring

1.  **Refactor `Household.make_decision`**:
    *   Remove the large manual `HouseholdConfigDTO` instantiation block.
    *   Replace it with a single call: `config_dto = create_config_dto(self.config_module, HouseholdConfigDTO)`.
    *   Ensure the data passed to `DecisionContext` for `goods_data` and `market_data` conforms to the new `TypedDict` structures. This may require casting or validation where the data is sourced.
2.  **Refactor `Firm.make_decision`**: Apply the same refactoring pattern as for `Household`.
3.  **Update Decision Engines**: Audit all decision engine classes (`RuleBased*`, `AIDriven*`) and update them to use the strongly-typed fields from the new DTOs instead of dictionary key access (e.g., `good['id']` instead of `good.get('id')`).

### Track C: Verification and Testing

1.  **Implement Purity Gate v2**: Update the assertions in `BaseDecisionEngine.make_decisions` as specified in 3.4.
2.  **Create Configuration Parity Test**:
    *   Create a new test file `tests/test_config_parity.py`.
    *   This test will import the real `config` module and the `HouseholdConfigDTO` and `FirmConfigDTO`.
    *   It will programmatically iterate through the fields of each DTO and assert that a corresponding uppercase attribute exists on the `config` module. This test will fail whenever a new field is added to a config DTO without updating the main config file, preventing drift.
3.  **Update Existing Tests**: Acknowledge that tests for decision engines will fail. Update them to pass a `DecisionContext` populated with correctly-typed mock DTOs instead of raw dictionaries.

## 5. 🚨 Risk & Impact Audit

-   **Test Impact (High)**: This is a breaking change for the test suite. All tests instantiating `DecisionContext` must be updated. However, the result will be more robust and readable tests.
-   **Configuration Risk (Mitigated)**: The `ConfigFactory` and the new `test_config_parity` test directly address the primary risk of configuration drift, turning a major liability into a managed, test-enforced contract.
-   **Data Structure Risk (Mitigated)**: Replacing raw dictionaries with `TypedDict`s enforces a strict data contract at the "Abstraction Wall," improving developer ergonomics and enabling better static analysis, which reduces the risk of runtime errors.
-   **Performance Impact (Negligible)**: The one-time cost of the `ConfigFactory` at the beginning of each agent's decision cycle is trivial compared to the overall simulation workload.

---

### [Routine] Mandatory Reporting

**Jules's Implementation Notes:**
-   During implementation, you must log any discrepancies found between the `goods.json` file structure and the proposed `GoodsDTO`.
-   All findings must be documented in a new file under `communications/insights/WO-135_Abstraction_Wall_Implementation_Log.md`.
-   Any new technical debt incurred must be logged in `design/TECH_DEBT_LEDGER.md` with the tag `WO-135-Follow-up`.
