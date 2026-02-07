```python
# modules/firm/api.py
from __future__ import annotations
from typing import TypedDict, List, Dict, Protocol, Any
from dataclasses import dataclass, field

from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from modules.finance.dtos import MoneyDTO
from simulation.models import Order # Assuming this can be imported

# =================================================================
# DTOs for State Representation
# =================================================================

@dataclass(frozen=True)
class ItemDTO:
    """Represents a quantity of a specific item with its quality."""
    item_id: str
    quantity: float
    quality: float = 1.0

@dataclass(frozen=True)
class ProductionInputDTO:
    """All necessary state for the ProductionDepartment to make a decision."""
    capital_stock: float
    automation_level: float
    productivity_factor: float
    hr_total_skill: float
    hr_avg_skill: float
    base_quality: float
    specialization: str
    input_inventory: Dict[str, float]
    config: Any # FirmConfigDTO

@dataclass(frozen=True)
class BrandSnapshotDTO:
    """Snapshot of brand state for sales decisions."""
    brand_awareness: float
    perceived_quality: float

@dataclass(frozen=True)
class MarketContextDTO:
    """Snapshot of relevant market data for sales decisions."""
    exchange_rates: Dict[CurrencyCode, float]
    # In a real scenario, this would be richer, e.g., with competitor prices
    # For now, keeping it as it was in the source.
    benchmark_rates: Dict[str, float]


@dataclass(frozen=True)
class SalesInputDTO:
    """All necessary state for the SalesDepartment to make a decision."""
    inventory: Dict[str, ItemDTO]
    last_prices: Dict[str, float]
    brand_snapshot: BrandSnapshotDTO
    specialization: str
    config: Any # FirmConfigDTO
    # For ROI calculation
    finance_revenue_this_turn: Dict[CurrencyCode, float]
    finance_last_revenue: float
    finance_last_marketing_spend: float
    marketing_budget_rate: float
    # For dynamic pricing
    inventory_last_sale_tick: Dict[str, int]


# =================================================================
# DTOs for Operation Results & Plans (State Deltas)
# =================================================================

@dataclass(frozen=True)
class ProductionResultDTO:
    """Describes the outcome of a production cycle."""
    produced_item: ItemDTO | None
    inputs_consumed: Dict[str, float] = field(default_factory=dict)
    capital_depreciation: float = 0.0
    automation_decay: float = 0.0

@dataclass(frozen=True)
class InvestmentPlanDTO:
    """Describes the cost and effect of a planned investment."""
    cost: MoneyDTO
    capital_increase: float = 0.0
    automation_increase: float = 0.0
    # For R&D, outcome is probabilistic, so we just return the cost plan
    # and the Firm will execute the probabilistic part.
    is_rd: bool = False

@dataclass(frozen=True)
class SalesActionsDTO:
    """Describes the sales and marketing actions to be taken."""
    orders_to_post: List[Order] = field(default_factory=list)
    new_marketing_budget: float = 0.0
    new_marketing_budget_rate: float = 0.0
    updated_prices: Dict[str, float] = field(default_factory=dict)

# =================================================================
# Stateless Engine Interfaces
# =================================================================

class IProductionEngine(Protocol):
    """A stateless engine for calculating production outcomes."""

    def produce(self, input_dto: ProductionInputDTO, current_time: int, technology_multiplier: float) -> ProductionResultDTO:
        """
        Calculates production output based on inputs.
        Returns a DTO describing the produced items and state deltas.
        """
        ...

    def plan_capex_investment(self, amount: float, config: Any) -> InvestmentPlanDTO:
        """Calculates the expected outcome of a CAPEX investment."""
        ...

    def plan_automation_investment(self, amount: float, config: Any) -> InvestmentPlanDTO:
        """Calculates the expected outcome of an automation investment."""
        ...

    def plan_rd_investment(self, amount: float) -> InvestmentPlanDTO:
        """Creates a plan for an R&D investment."""
        ...


class ISalesEngine(Protocol):
    """A stateless engine for calculating sales and marketing actions."""

    def plan_sales_posts(
        self,
        input_dto: SalesInputDTO,
        market: Any, # OrderBookMarket
        current_tick: int
    ) -> List[Order]:
        """
        Determines what inventory to sell and at what price.
        Returns a list of Order objects to be placed.
        """
        ...

    def plan_marketing_strategy(
        self,
        input_dto: SalesInputDTO,
        market_context: MarketContextDTO,
        firm_primary_balance: float
    ) -> tuple[float, float]:
        """
        Calculates the new marketing budget and budget rate based on ROI.
        Returns (new_marketing_budget, new_marketing_budget_rate).
        """
        ...

    def apply_dynamic_pricing(
        self,
        orders: List[Order],
        input_dto: SalesInputDTO,
        estimated_unit_costs: Dict[str, float],
        current_tick: int
    ) -> tuple[List[Order], Dict[str, float]]:
        """
        Applies discounts to stale inventory.
        Returns a new list of modified orders and a dict of updated prices.
        """
        ...
```
# Technical Specification: Decoupling Firm Departments

**Document Version:** 1.0
**Date:** 2026-02-07
**Author:** Gemini Scribe

## 1. Overview & Mandate

This specification outlines a major architectural refactor of the `Firm` agent. The primary goal is to **decouple the `ProductionDepartment` and `SalesDepartment` from the main `Firm` class, eliminating direct parent object access (`self.firm`)**.

This change directly addresses the critical architectural risks identified in the **Pre-Flight Audit**, transforming the departments from stateful, tightly-coupled components into **pure, stateless "Engines"**. The `Firm` class will evolve into an orchestrator, managing state and executing the plans generated by these engines.

## 2. Architectural Vision: The Orchestrator-Engine Pattern

The new architecture follows a strict data-flow pattern:

1.  **State Aggregation (Firm)**: The `Firm` agent gathers its complete internal state (`capital_stock`, `inventory`, `brand_awareness`, etc.).
2.  **DTO Creation (Firm)**: It packages this state into immutable `ProductionInputDTO` and `SalesInputDTO` objects.
3.  **Stateless Calculation (Engines)**: The `Firm` calls methods on the `ProductionEngine` and `SalesEngine`, passing these DTOs. The engines are pure-functional calculators; they contain no state and have no side effects.
4.  **Result DTO Return (Engines)**: The engines return `ProductionResultDTO` and `SalesActionsDTO` objects, which are data structures describing the *intended* state changes (e.g., `capital_depreciation: 10.0`) and actions (e.g., `orders_to_post: [...]`).
5.  **Orchestration & State Mutation (Firm)**: The `Firm` receives the result DTOs. It is solely responsible for applying the state changes to itself and executing the actions, such as calling the `FinanceDepartment` or placing orders on the market.

This pattern enforces a clear separation of concerns:
-   **Engines**: Contain the "how-to" business logic (e.g., Cobb-Douglas formula).
-   **Firm**: Contains the state and orchestrates the "what-to-do" sequence.

## 3. Interface & DTO Definitions

The full API contract is defined in `modules/firm/api.py`. Key components are summarized below.

### 3.1. Input DTOs (State Snapshots)

-   `ProductionInputDTO`: Contains all state needed for production calculations (capital, automation, skills, inventory, config).
-   `SalesInputDTO`: Contains all state for sales and marketing (inventory, prices, brand snapshot, financial history for ROI, config).

### 3.2. Result/Action DTOs (State Deltas & Plans)

-   `ProductionResultDTO`: Describes the outcome of production (new items, consumed inputs, depreciation).
-   `InvestmentPlanDTO`: Describes the cost and expected outcome of an investment (CAPEX, R&D).
-   `SalesActionsDTO`: Describes sales actions (orders to post, new marketing budget).

### 3.3. Stateless Engine Interfaces

-   `IProductionEngine`: A protocol defining methods like `produce(...) -> ProductionResultDTO` and `plan_capex_investment(...) -> InvestmentPlanDTO`.
-   `ISalesEngine`: A protocol defining methods for planning sales posts, marketing, and dynamic pricing, all returning action DTOs.

## 4. Pseudo-Code: Before & After

To illustrate the change, we examine the `produce` and `invest_in_capex` logic.

### 4.1. Production Logic

#### **Before (Coupled)**

```python
# In Firm class
def produce(self, ...):
    # Directly calls the coupled component
    self.production.produce(current_time, ...)

# In ProductionDepartment class
def produce(self, ...):
    # Direct read/write access to parent state
    self.firm.capital_stock *= 0.99 # Mutates parent state
    total_labor_skill = self.firm.hr.get_total_labor_skill() # Accesses sibling component
    # ... calculation ...
    self.firm.add_item(...) # Mutates parent inventory
```

#### **After (Decoupled Orchestrator-Engine)**

```python
# In Firm class
def produce(self, current_time: int, technology_manager: Any):
    # 1. State Aggregation & DTO Creation
    input_dto = ProductionInputDTO(
        capital_stock=self.capital_stock,
        automation_level=self.automation_level,
        hr_total_skill=self.hr.get_total_labor_skill(),
        # ... other fields ...
        config=self.config
    )
    tech_multiplier = technology_manager.get_productivity_multiplier(self.id)

    # 2. Stateless Calculation
    result_dto = self.production_engine.produce(input_dto, current_time, tech_multiplier)

    # 3. State Mutation (Orchestration)
    self.capital_stock -= result_dto.capital_depreciation
    self.automation_level -= result_dto.automation_decay

    for item_id, consumed_qty in result_dto.inputs_consumed.items():
        self.input_inventory[item_id] -= consumed_qty

    if result_dto.produced_item:
        self.add_item(
            result_dto.produced_item.item_id,
            result_dto.produced_item.quantity,
            quality=result_dto.produced_item.quality
        )

# In ProductionEngine (New Stateless Class)
class ProductionEngine:
    def produce(...) -> ProductionResultDTO:
        # NO self.firm. Pure calculation based on input_dto.
        depreciation = input_dto.capital_stock * input_dto.config.capital_depreciation_rate
        # ... calculation ...
        produced_item = ItemDTO(...)
        inputs_consumed = {...}

        # Return a data structure describing all changes
        return ProductionResultDTO(
            produced_item=produced_item,
            inputs_consumed=inputs_consumed,
            capital_depreciation=depreciation,
            # ... other deltas ...
        )
```

### 4.2. Investment Logic (Inter-Department Communication)

#### **Before (Hidden Dependency)**

```python
# In ProductionDepartment class
def invest_in_capex(self, amount: float, ...) -> bool:
    # Directly calls sibling component through parent
    if self.firm.finance.invest_in_capex(amount, ...):
        # ... calculates added_capital ...
        self.add_capital(added_capital) # Mutates parent state
        return True
    return False
```

#### **After (Explicit Orchestration)**

```python
# In Firm class
def _execute_internal_order(self, order: Order, ...):
    if order.order_type == "INVEST_CAPEX":
        amount = order.monetary_amount['amount']

        # 1. Get a plan from the stateless engine
        plan_dto = self.production_engine.plan_capex_investment(amount, self.config)

        # 2. Firm orchestrates the two-step process
        # Step A: Call the Finance component
        payment_successful = self.finance.invest_in_capex(plan_dto.cost, ...)

        # Step B: Apply state change if payment succeeded
        if payment_successful:
            self.capital_stock += plan_dto.capital_increase

# In ProductionEngine (New Stateless Class)
class ProductionEngine:
    def plan_capex_investment(self, amount: float, config: Any) -> InvestmentPlanDTO:
        # Pure calculation, no side effects
        efficiency = 1.0 / config.capital_to_output_ratio
        added_capital = amount * efficiency
        return InvestmentPlanDTO(
            cost=MoneyDTO(amount=amount, currency=DEFAULT_CURRENCY),
            capital_increase=added_capital
        )
```

## 5. Risk Mitigation & Audit Compliance

This design directly addresses the critical risks identified in the pre-flight audit:

-   **Risk: Direct Contradiction of `ARCH_AGENTS.md`**: **Mitigated**. This spec explicitly acknowledges the deviation and defines a new, superior pattern (Orchestrator-Engine) to replace the problematic stateful component model. The `ARCH_AGENTS.md` file will be updated to reflect this new canonical architecture.
-   **Risk: Hidden Inter-Department Dependencies**: **Mitigated**. The `Firm` is now the explicit orchestrator. `ProductionEngine` no longer calls `Finance`; it returns an `InvestmentPlanDTO`, and the `Firm` executes the financial transaction and subsequent state change. Communication is no longer implicit.
-   **Risk: Bi-Directional State Mutation**: **Mitigated**. Engines are now pure functions that return state-delta DTOs. All state mutation is centralized within the `Firm` class, creating a predictable, one-way data flow.
-   **Risk: Widespread Test Suite Invalidation**: **Acknowledged**. The project plan must include a dedicated work package for rewriting all tests related to the `Firm` agent. **Benefit**: The new engine classes are highly testable in isolation. A test for `ProductionEngine.produce` only requires constructing an `ProductionInputDTO` and asserting the output, eliminating the need for complex `Firm` object mocks.

## 6. Verification & Test Plan

1.  **Unit Tests (Engines)**: Create comprehensive unit tests for `ProductionEngine` and `SalesEngine`. Test each method by providing a variety of `InputDTO`s (including edge cases) and verifying the contents of the returned `ResultDTO`.
2.  **Integration Tests (Firm Orchestrator)**: Refactor existing `Firm` tests to align with the new Orchestrator-Engine pattern. Test the `Firm`'s ability to correctly interpret `ResultDTO`s and apply state changes.
3.  **Golden Data Fixtures**: Create `pytest` fixtures that provide realistic, populated instances of `ProductionInputDTO` and `SalesInputDTO`. These will serve as the "golden samples" for testing engine logic.
4.  **Protocol Compliance**: Ensure all inventory mutations within the `Firm` class's new orchestration logic respect the `IInventoryHandler` protocol (`add_item`, `remove_item`).

## 7. Mandatory Reporting: Insights & Technical Debt

-   **Insight**: This refactoring clarifies a core architectural role. The `Firm` class embodies the agent's "System 2" strategic thinking (what to do and when), while the new stateless "Engines" represent the "System 1" physics and business rules (how to calculate outcomes). This separation makes the logic cleaner and more scalable.
-   **Technical Debt Addressed**:
    -   **TD-A (Implicit Coupling)**: The stateful component pattern with parent pointers is eliminated.
    -   **TD-B (Untestable Components)**: Components are now pure and easily testable in isolation.
-   **New Technical Debt Incurred**:
    -   **TD-C (Orchestrator Complexity)**: The `Firm` class becomes more complex as it now contains all state mutation and orchestration logic. This is a deliberate trade-off for architectural purity and must be managed with clear, well-documented methods.
-   **Report Location**: A record of this has been logged to `communications/insights/REF-001-Firm-Decoupling.md`.
