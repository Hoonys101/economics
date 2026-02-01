# Spec: Immutable Market Snapshot for Agent Decisions (TD-182)

## 1. Overview

### 1.1. Problem
The current architecture passes raw, mutable market objects directly to agent `make_decision` methods via the `DecisionInputDTO`. This practice violates core software design principles, including encapsulation and the Single Responsibility Principle. It creates "God Object" agents with the ability to directly inspect and mutate market state, leading to tight coupling, untraceable bugs, and fragile tests. The provided `[AUTO-AUDIT FINDINGS]` for TD-182 correctly identify this as a critical architectural risk.

### 1.2. Solution
This specification mandates the refactoring of the agent decision-making interface to enforce immutability and clear separation of concerns. The `markets: Dict[str, Any]` field will be removed from `DecisionInputDTO` and replaced with a mandatory, comprehensive, and immutable `MarketSnapshotDTO`. This snapshot will be constructed by a high-level simulation orchestrator *before* being passed to any agent, ensuring agents act as pure decision-makers based on read-only data.

## 2. DTO Redesign

The `DecisionInputDTO` in `simulation/dtos/api.py` will be modified as follows.

### 2.1. `DecisionInputDTO` Refactoring

**Before:**
```python
@dataclass
class DecisionInputDTO:
    """
    Standardized input DTO for agent decision-making.
    Encapsulates all external system inputs passed to make_decision.
    """
    markets: Dict[str, Any] # <--- CRITICAL RISK: MUTABLE
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    # ... other fields
    market_snapshot: Optional[MarketSnapshotDTO] = None # <--- Optional, allows inconsistent use
```

**After:**
```python
# In simulation/dtos/api.py
from modules.system.api import MarketSnapshotDTO # Ensure this is the canonical DTO

@dataclass
class DecisionInputDTO:
    """
    Standardized input DTO for agent decision-making.
    Encapsulates all external system inputs passed to make_decision.
    Agents operate on IMMUTABLE snapshots of the world.
    """
    # REMOVED: markets: Dict[str, Any]
    market_snapshot: MarketSnapshotDTO # <--- MANDATORY & IMMUTABLE
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any] # Note: Should also be audited for immutability, but outside TD-182 scope.
    current_time: int
    fiscal_context: Optional[FiscalContext] = None
    macro_context: Optional[MacroFinancialContext] = None
    stress_scenario_config: Optional[Any] = None
    government_policy: Optional[GovernmentPolicyDTO] = None
    agent_registry: Optional[Dict[str, int]] = None
```

### 2.2. Canonical `MarketSnapshotDTO`
The `MarketSnapshotDTO` (defined in `modules.system.api` and composed of smaller snapshots like `HousingMarketSnapshotDTO` from `modules.household.api`) will serve as the single source of truth for market state during the decision phase. It is assumed to be sufficiently comprehensive. If any agent requires data not present in the current snapshot, the snapshot's definition must be expanded.

```python
# from modules.household.api
@dataclass
class HousingMarketUnitDTO:
    unit_id: str
    price: float
    quality: float

@dataclass
class HousingMarketSnapshotDTO:
    for_sale_units: List[HousingMarketUnitDTO]
    avg_rent_price: float
    avg_sale_price: float

# ... other sub-snapshots (Loan, Labor)

# from modules.system.api
@dataclass
class MarketSnapshotDTO:
    """A comprehensive, read-only snapshot of all relevant markets."""
    housing: HousingMarketSnapshotDTO
    loan: LoanMarketSnapshotDTO
    labor: LaborMarketSnapshotDTO
    # TBD (Team Leader Review Required): Add other markets as needed (e.g., goods, stocks)
    # stock_market: StockMarketSnapshotDTO
    # goods_markets: Dict[str, GoodsMarketSnapshotDTO]
```

## 3. Orchestration Logic (Pseudo-code)

The main simulation loop (e.g., in a `Simulation` or `TickScheduler` class) must be modified to include a snapshot generation step.

```python
# In Simulation orchestrator (e.g., Simulation.run_tick)

# --- PRE-DECISION PHASE ---
# 1. Create Market Snapshot
market_snapshot_dto = self.create_market_snapshot()

# 2. Prepare other context DTOs
# ... (e.g., government_policy_dto)

# --- DECISION PHASE ---
all_orders = []
for agent in self.agents.values():
    if not agent.is_active:
        continue

    # 3. Create the immutable input DTO
    decision_input = DecisionInputDTO(
        market_snapshot=market_snapshot_dto, # Pass the pre-built snapshot
        goods_data=self.goods_data,
        market_data=self.market_data, # Legacy data, to be reviewed later
        current_time=self.time,
        # ... other contexts
    )

    # 4. Agent makes decision based on the snapshot
    orders, _ = agent.make_decision(decision_input)
    all_orders.extend(orders)

# ... rest of the simulation tick

def create_market_snapshot(self) -> MarketSnapshotDTO:
    """
    This new method is responsible for querying market states and building the DTO.
    This logic is REMOVED from the agent.
    """
    # Housing Snapshot
    housing_market_obj = self.markets.get("housing")
    for_sale_units = []
    if housing_market_obj and hasattr(housing_market_obj, "sell_orders"):
        for item_id, sell_orders in housing_market_obj.sell_orders.items():
            if item_id.startswith("unit_") and sell_orders:
                best_order = sell_orders[0]
                for_sale_units.append(HousingMarketUnitDTO(
                    unit_id=item_id,
                    price=best_order.price,
                    quality=1.0 # TBD: Fetch quality from a central registry
                ))
    housing_data = self.market_data.get("housing_market", {})
    housing_snapshot = HousingMarketSnapshotDTO(
        for_sale_units=for_sale_units,
        avg_rent_price=housing_data.get("avg_rent_price", 100.0),
        avg_sale_price=housing_data.get("avg_sale_price", 24000.0)
    )

    # Loan Snapshot
    loan_data = self.market_data.get("loan_market", {})
    loan_snapshot = LoanMarketSnapshotDTO(
        interest_rate=loan_data.get("interest_rate", 0.05)
    )

    # Labor Snapshot
    labor_data = self.market_data.get("labor", {})
    labor_snapshot = LaborMarketSnapshotDTO(
        avg_wage=labor_data.get("avg_wage", 0.0)
    )

    # Assemble the final DTO
    return MarketSnapshotDTO(
        housing=housing_snapshot,
        loan=loan_snapshot,
        labor=labor_snapshot
    )
```

## 4. Agent `make_decision` Refactoring

The `Household.make_decision` method will be significantly simplified.

**Before:**
```python
# In simulation.core_agents.py
class Household(BaseAgent, ILearningAgent):
    def make_decision(self, input_dto: DecisionInputDTO) -> ...:
        # ...
        # Housing Snapshot
        housing_market_obj = markets.get("housing") # <--- Direct market access
        for_sale_units = []
        if housing_market_obj and hasattr(housing_market_obj, "sell_orders"):
             for item_id, sell_orders in housing_market_obj.sell_orders.items():
                # ... logic to parse orders and create DTOs ...
        # ... more logic to build Loan and Labor snapshots ...
```

**After:**
```python
# In simulation.core_agents.py
class Household(BaseAgent, ILearningAgent):
    def make_decision(self, input_dto: DecisionInputDTO) -> ...:
        # Unpack input_dto
        # REMOVED: markets = input_dto.markets
        market_snapshot = input_dto.market_snapshot # <--- Use the pre-built snapshot
        # ...

        # The orchestration DTO for the DecisionUnit is now built from the snapshot
        orchestration_context = OrchestrationContextDTO(
            market_snapshot=market_snapshot, # Pass the snapshot down
            current_time=input_dto.current_time,
            stress_scenario_config=input_dto.stress_scenario_config,
            config=self.config
        )

        # Delegate to DecisionUnit (Stateless)
        self._econ_state, refined_orders = self.decision_unit.orchestrate_economic_decisions(
            state=self._econ_state,
            context=orchestration_context,
            initial_orders=initial_orders
        )

        return refined_orders, chosen_tactic_tuple
```
The logic for creating `HousingMarketSnapshotDTO`, `LoanMarketSnapshotDTO`, etc., is completely removed from the agent. The agent now only consumes the `market_snapshot` provided in the `input_dto`.

## 5. Test Impact and Migration Plan

- **Breaking Change**: This is a fundamental, breaking change. All tests that call `agent.make_decision` will fail.
- **Migration Steps**:
  1.  Identify all tests that instantiate `DecisionInputDTO`.
  2.  Remove the `markets` argument from the DTO instantiation.
  3.  Instead of creating mock market objects with complex internal state (e.g., `mock_market.sell_orders`), tests must now create an instance of `MarketSnapshotDTO` and its sub-DTOs with the required test data.
  4.  Pass this `market_snapshot` instance into the `DecisionInputDTO`.

- **Benefit**: This refactoring decouples tests from the implementation details of market objects. Tests will become more robust, easier to write, and less likely to break when market internals are changed.

## 6. Risk & Impact Audit

- **Addressed Risk (Mutation)**: By removing direct market access, the risk of agents causing unintended state mutations is eliminated. The simulation flow becomes predictable and auditable.
- **Addressed Risk (SRP)**: The responsibility of "creating a view of the market" is moved from the Agent to the Simulation Orchestrator, where it belongs. Agents are now correctly focused only on "making a decision".
- **Data Completeness Constraint**: The primary implementation constraint is to ensure the new `MarketSnapshotDTO` is a complete superset of all data currently being accessed by agents from the raw market objects. A thorough audit of all `make_decision` implementations across all agent types (`Firm`, etc.) is required to guarantee no data is lost in the transition. Any missing data points must be added to the snapshot DTOs.
