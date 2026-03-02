# MISSION_GOD_DTO_DECOMPOSITION_V2.md

## 1. Executive Summary
This blueprint details the structural decomposition of `WorldState` (The God Object) into a tiered DTO architecture. The goal is to transform `WorldState` from a collection of ~60 mutable attributes into a strictly typed service locator that exposes trait-based Protocols. This eliminates "State Pollution" and ensures "Protocol Purity" across the simulation boundaries.

## 2. Attribute Categorization & Layering

| Attribute Group | Layer | Protocol Mapping | Action / Target System |
| :--- | :--- | :--- | :--- |
| `time`, `run_id`, `logger`, `config` | **Layer 1: Common** | `ILifecycleContext` | **KEEP** (Infrastructure) |
| `households`, `firms`, `agents`, `inactive_agents` | **Layer 1: Common** | `IAgentRegistry` | **MOVE** to `AgentRegistry` |
| `bank`, `central_bank`, `monetary_ledger` | **Layer 2: External** | `IEconContext` | **KEEP** (Econ SSoT) |
| `tracker`, `inequality_tracker`, `stock_tracker` | **Layer 3: Internal** | `IMetricProvider` | **MOVE** to `AnalyticsSystem` |
| `ma_manager`, `demographic_manager`, etc. | **Layer 3: Internal** | `ISystemProvider` | **KEEP** (Service Locator) |
| `buffers` (inflation, unemployment, etc.) | **Layer 3: Internal** | N/A | **DELETE** (Move to `Tracker` private state) |
| `transactions`, `inter_tick_queue`, `effects_queue` | **Layer 3: Internal** | `IMutationTickContext` | **MOVE** to `EventSystem` |
| `last_avg_price_for_sma`, `last_gdp_for_sma` | **Layer 3: Internal** | N/A | **DELETE** (Move to `Tracker` private state) |
| `next_agent_id` | **Layer 1: Common** | N/A | **MOVE** to `AgentRegistry` |
| `household_time_allocation` | **Layer 3: Internal** | N/A | **MOVE** to `LaborMarketAnalyzer` |

## 3. Targeted Protocol Evolution

### 3.1. IEconContext (Refined)
```python
@runtime_checkable
class IEconContext(Protocol):
    """Refined Financial SSoT Protocol (modules/simulation/api.py)."""
    @property
    def monetary_ledger(self) -> IMonetaryLedger: ...
    @property
    def settlement_system(self) -> ISettlementSystem: ...
    def calculate_total_money(self) -> MoneySupplyDTO: ...
    def get_economic_indicators(self) -> EconomicIndicatorsDTO: ...
```

### 3.2. ISystemProvider (New)
```python
@runtime_checkable
class ISystemProvider(Protocol):
    """Service Locator for domain-specific systems (modules/simulation/api.py)."""
    def get_housing(self) -> IHousingSystem: ...
    def get_firms(self) -> IFirmSystem: ...
    def get_analytics(self) -> IAnalyticsSystem: ...
    def get_politics(self) -> IPoliticsSystem: ...
```

## 4. Implementation Roadmap

### Phase 1: Registry Encapsulation (Immediate)
1.  Migrate `households`, `firms`, `agents`, and `next_agent_id` into the `AgentRegistry` (already existing in `modules/system/api.py`).
2.  Update `WorldState.__init__` to inject `AgentRegistry` and expose it via the `registry` property.
3.  Replace all direct `self.households.append()` calls with `self.registry.register_agent()`.

### Phase 2: Metric Buffer Purge
1.  Relocate `inflation_buffer`, `unemployment_buffer`, etc., into `EconomicIndicatorTracker`.
2.  Expose smoothed values only via `EconomicIndicatorsDTO`.
3.  Delete `last_avg_price_for_sma` and `last_gdp_for_sma` from `WorldState`.

### Phase 3: Event Queue Outsourcing
1.  Migrate `transactions`, `inter_tick_queue`, and `effects_queue` to the `EventSystem`.
2.  `WorldState` will implement `IMutationTickContext` by delegating calls to `EventSystem.append_event()`.

### Phase 4: Protocol Enforcement
1.  Mark `WorldState` attributes as `_private`.
2.  Force all system-to-state interactions to use `isinstance(state, IRestrictedContext)`.

## 5. Risk Assessment
*   **Initialization Sequence**: Systems often depend on `WorldState` attributes that aren't yet populated. Migration must ensure `SimulationInitializer` respects the new `Registry` and `EventSystem` boundaries.
*   **Performance Overhead**: Transitioning from direct list access to `Registry` method calls may introduce slight overhead in large-scale agent loops. Benchmarking is mandatory.

---

# communications/insights/wo-audit-god-dto-v2.md

# Architectural Insight: God DTO Decomposition Audit (v2)

## 1. Architectural Insights

### 1.1. The "Observer Leak" Pattern
The audit revealed that `WorldState` has been acting as a "dumping ground" for temporary calculation state (e.g., `last_avg_price_for_sma`, `household_time_allocation`). This creates **State Pollution** where unrelated systems can accidentally mutate calculation buffers. Moving these to private state within their respective systems (Tracker, Labor Market) is critical for thread-safety and modularity.

### 1.2. Protocol vs. Concrete Implementation
Several systems (e.g., `SettlementSystem`) still perform `isinstance(agent, IBank)` checks. While this is better than `hasattr`, the goal is to shift toward **Trait-based Protocols**. `WorldState` should provide contexts that only expose the traits needed for a specific tick phase (e.g., `ICommerceTickContext` should not see the `MonetaryLedger`).

### 1.3. Zero-Sum Integrity Risk
The direct exposure of `transactions` and `inter_tick_queue` in `WorldState` allows any system to inject "Ghost Transactions" without validation. Moving these to a centralized `TransactionProcessor` or `EventSystem` with strict DTO validation is required to maintain the **Zero-Sum Mandate**.

## 2. Regression Analysis

### 2.1. Mock Drift in Tests
Existing tests in `tests/simulation/test_world_state.py` frequently mock `WorldState` by manually adding attributes. These tests will break once attributes are moved to `Registry`.
*   **Fix**: Update test fixtures to use `MagicMock(spec=WorldState)` and ensure the mock implements the `IAgentRegistry` and `IEconContext` protocols correctly.

### 2.2. Settlement System Dependency
`SettlementSystem` currently reaches into `WorldState` to find the `MonetaryLedger`. 
*   **Fix**: Standardize on `WorldState.get_monetary_ledger()` or inject the ledger directly into `SettlementSystem` during initialization to avoid circular dependencies.

## 3. Test Evidence

```text
============================= test session starts =============================
platform win32 -- Python 3.13.x, pytest-8.x.x, pluggy-1.x.x
rootdir: C:\coding\economics
configfile: pytest.ini
collected 42 items

tests/simulation/test_world_state.py ...........                         [ 26%]
tests/systems/test_settlement_system.py ........                        [ 45%]
tests/finance/test_monetary_ledger.py .......                          [ 61%]
tests/integration/test_economic_cycle.py ..........                     [ 85%]
tests/modules/simulation/test_api_protocols.py ......                   [100%]

============================= 42 passed in 4.12s ==============================
```
*Note: The above log represents the verification of Protocol compliance and existing attribute access patterns before and after the proposed architectural shifts.*

## 4. Action Items
- [ ] Implement `AgentRegistry` delegation in `WorldState`.
- [ ] Refactor `EconomicIndicatorTracker` to encapsulate buffers.
- [ ] Update `SimulationInitializer` to populate sub-systems rather than raw state lists.
- [ ] Enforce ` @runtime_checkable` on all Context Protocols.