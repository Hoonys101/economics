# Unified Housing Decision System (`HousingPlanner`)

## 1. Overview

**Goal**: To resolve technical debt (TD-065) by consolidating the duplicated and scattered housing decision logic from `DecisionUnit` and `HouseholdSystem2Planner` into a single, unified, and stateless source of truth: the `HousingPlanner` system.

**Problem**: Currently, a household's decision to buy, sell, or rent property is determined in multiple places, creating high maintenance costs and risk of inconsistent behavior. The existing `HousingSystem` is also too tightly coupled with the main `Simulation` engine, violating SRP and making it difficult to test.

**Solution**: This refactoring introduces a clear separation of concerns:
1.  **`HousingPlanner` (New)**: A stateless component that contains all business logic for housing *decisions*. It receives data via DTOs and returns a recommended `HousingDecisionDTO`.
2.  **Simulation Engine (Orchestrator)**: Gathers data, calls the `HousingPlanner` for a decision, and then translates that decision into a concrete action (e.g., placing an order on the market).
3.  **`HousingSystem` (Refactored)**: Continues its role of processing the *consequences* of housing status (rent, maintenance, foreclosure) but is no longer involved in decision-making.

This design decouples decision logic from execution, improves testability, and creates a clear, traceable flow from intent to action.

## 2. Architecture

```mermaid
graph TD
    subgraph Simulation Engine Loop
        A[1. Gather Agent & Market Data] --> B{2. For each Household};
    end

    subgraph "HousingPlanner (Stateless)"
        C[3. Call HousingPlanner.evaluate_and_decide(household_dto, market_dto)];
    end
    
    subgraph "Execution Systems"
        D[4. Receive HousingDecisionDTO] --> E{Translate to Market Order};
        E --> F[Housing Market];
    end

    B --> C;
    C --> D;

    style C fill:#f9f,stroke:#333,stroke-width:2px
```

## 3. Detailed Logic (Pseudo-code)

The core of the new system is the `evaluate_and_decide` method. It follows a clear priority hierarchy.

```python
# In modules.housing.planner.HousingPlanner

def evaluate_and_decide(household: HouseholdHousingStateDTO, market: HousingMarketStateDTO, config: AppConfig) -> HousingDecisionDTO:
    """
    Determines the optimal housing action for a household based on its state and market conditions.
    This function is PURE and has NO side effects.
    """

    # --- Priority 1: Homelessness ---
    # The most urgent need is shelter.
    if household.is_homeless:
        # Find the cheapest, minimally acceptable rental unit.
        affordable_rentals = [
            u for u in market.units_for_rent
            if u.rent_price <= household.income * config.housing.RENT_TO_INCOME_RATIO_MAX
        ]
        if affordable_rentals:
            cheapest_rental = min(affordable_rentals, key=lambda u: u.rent_price)
            return HousingDecisionDTO(
                agent_id=household.id,
                action=HousingActionType.SEEK_RENTAL,
                target_unit_id=cheapest_rental.id,
                justification="Agent is homeless and can afford rent."
            )
        else:
            return HousingDecisionDTO(agent_id=household.id, action=HousingActionType.STAY, justification="Agent is homeless but cannot afford any available rentals.")

    # --- Priority 2: Financial Distress (Owner) ---
    # An owner who is financially unstable should liquidate their property.
    if household.owned_property_ids:
        # Assuming an agent owns at most one property for now
        owned_property_id = household.owned_property_ids[0] 
        if household.assets < household.income * config.housing.FINANCIAL_DISTRESS_ASSET_THRESHOLD_MONTHS:
             return HousingDecisionDTO(
                agent_id=household.id,
                action=HousingActionType.SELL_PROPERTY,
                sell_unit_id=owned_property_id,
                justification="Agent is in financial distress; liquidating property."
            )

    # --- Priority 3: Desire to Upgrade (Renter to Owner) ---
    # A financially stable renter may want to buy a house.
    if household.residing_property_id and not household.owned_property_ids: # Is a renter
        affordable_homes = [
            h for h in market.units_for_sale 
            if is_purchase_affordable(h, household, config)
        ]
        if affordable_homes:
            best_home = min(affordable_homes, key=lambda h: h.for_sale_price) # Simplistic choice
            return HousingDecisionDTO(
                agent_id=household.id,
                action=HousingActionType.SEEK_PURCHASE,
                target_unit_id=best_home.id,
                justification="Agent is a renter and can afford to purchase a home."
            )

    # --- Default Action: Stay ---
    # If no other conditions are met, maintain the status quo.
    return HousingDecisionDTO(agent_id=household.id, action=HousingActionType.STAY, justification="No urgent need or opportunity to move.")

def is_purchase_affordable(home, household, config):
    down_payment = home.for_sale_price * config.finance.MORTGAGE_DOWN_PAYMENT_RATE
    monthly_payment = calculate_mortgage_payment(home.for_sale_price, config)
    
    has_down_payment = household.assets >= down_payment
    can_afford_monthly = monthly_payment < household.income * config.housing.MORTGAGE_TO_INCOME_RATIO_MAX

    return has_down_payment and can_afford_monthly
```

## 4. Interface Specification (`api.py`)

The public contract for the housing module will be defined in `modules/housing/api.py`.

### DTOs (Data Transfer Objects)
-   **`HouseholdHousingStateDTO`**: Snapshot of a household's financial and housing status.
-   **`RealEstateUnitDTO`**: Snapshot of a single property's market and ownership status.
-   **`HousingMarketStateDTO`**: Collection of all properties currently on the market.
-   **`HousingActionType(Enum)`**: Defines the possible decisions (`STAY`, `SEEK_RENTAL`, `SEEK_PURCHASE`, `SELL_PROPERTY`).
-   **`HousingDecisionDTO`**: The output of the planner, containing the agent's ID, the chosen action, and target property IDs.

### Interface (`IHousingPlanner`)
-   A single abstract method `evaluate_and_decide` that accepts the state DTOs and returns a decision DTO.

## 5. Verification Plan

-   **Unit Tests**: The `HousingPlanner` will be unit-tested extensively. Since it's a pure function, tests will involve passing various `HouseholdHousingStateDTO` and `HousingMarketStateDTO` objects and asserting the returned `HousingDecisionDTO` is correct.
-   **Golden Data Strategy**:
    -   **Usage**: Tests will heavily leverage existing fixtures like `golden_households` to generate realistic `HouseholdHousingStateDTO`s.
    -   **Mocks**: No `MagicMock` is needed for the planner's unit tests. For *integration tests*, the `Simulation` engine's test will mock `IHousingPlanner` to return specific decisions, allowing verification of the engine's orchestration logic (e.g., ensuring a `SEEK_PURCHASE` decision correctly generates a market buy order).
-   **Integration Tests**: New integration tests will be required to verify the `Simulation` engine correctly calls the planner and processes its output. Existing tests for `DecisionUnit` will be deprecated.

### 🚨 Schema Change Notice
Any modification to `HouseholdHousingStateDTO` or `RealEstateUnitDTO` will require updating the golden data fixtures. The `scripts/fixture_harvester.py` script should be used to regenerate these fixtures from a baseline simulation snapshot to ensure data integrity.

## 6. Risk & Impact Audit

This design directly addresses the risks identified in the pre-flight audit:

-   **[Mitigated] God Class Dependency**: The `HousingPlanner` is fully decoupled from the `Simulation` object. It operates exclusively on serializable DTOs, making it independently testable and reusable.
-   **[Mitigated] Single Responsibility Principle Violation**: Responsibilities are now clearly separated: `HousingPlanner` (decides), `Simulation` (orchestrates), `Market` (transacts), `HousingSystem` (maintains).
-   **[Mitigated] Implicit State Contracts**: The planner produces an explicit `HousingDecisionDTO`, eliminating direct state manipulation. The engine is now the single, traceable point of state change based on these decisions.
-   **[Considered] Circular Dependency**: The introduction of `modules/housing/api.py` isolates housing-related contracts, preventing new import cycles between subsystems and the core engine.
-   **[Addressed] Fragile Integration Tests**: The testing strategy acknowledges that old tests will break. It proposes a more robust, two-tiered approach: simple, stable unit tests for the complex decision logic, and focused integration tests for the simpler orchestration logic.

---

## 7. Insight & Technical Debt Recording

- **Insight**: This refactoring provides a blueprint for decoupling other complex decision systems (e.g., job seeking, consumption) from the main engine, paving the way for a more modular and maintainable architecture.
- **Action**: All insights and discovered technical debt during implementation must be logged in a new file under `communications/insights/WO-XXX-Housing-Refactor.md` to avoid merge conflicts with shared documents.

```python
# Path: modules/housing/api.py
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any

try:
    from pydantic.dataclasses import dataclass
except ImportError:
    from dataclasses import dataclass


# --- Data Transfer Objects (DTOs) ---

@dataclass(frozen=True)
class HouseholdHousingStateDTO:
    """A snapshot of a household's state relevant to housing decisions."""
    id: int
    assets: float
    income: float
    is_homeless: bool
    residing_property_id: Optional[int]
    owned_property_ids: List[int]
    needs: Dict[str, float]


@dataclass(frozen=True)
class RealEstateUnitDTO:
    """A snapshot of a real estate unit's state."""
    id: int
    owner_id: Optional[int]
    estimated_value: float
    rent_price: float
    for_sale_price: float
    on_market_for_rent: bool
    on_market_for_sale: bool


@dataclass(frozen=True)
class HousingMarketStateDTO:
    """A snapshot of the housing market."""
    units_for_sale: List[RealEstateUnitDTO]
    units_for_rent: List[RealEstateUnitDTO]


class HousingActionType(str, Enum):
    """Enumerates the possible housing decisions an agent can make."""
    STAY = "STAY"
    SEEK_RENTAL = "SEEK_RENTAL"
    SEEK_PURCHASE = "SEEK_PURCHASE"
    SELL_PROPERTY = "SELL_PROPERTY"


@dataclass(frozen=True)
class HousingDecisionDTO:
    """Represents the output of the housing planner."""
    agent_id: int
    action: HousingActionType
    target_unit_id: Optional[int] = None
    sell_unit_id: Optional[int] = None
    justification: str = ""


# --- Interfaces (Abstract Base Classes) ---

class IHousingPlanner(ABC):
    """
    Interface for the system that makes housing decisions for households.
    This contract ensures the planner is stateless and decoupled from the engine.
    """

    @abstractmethod
    def evaluate_and_decide(
        self,
        household: HouseholdHousingStateDTO,
        market: HousingMarketStateDTO,
        config: Any, # Using Any to avoid circular dependency with full config object
    ) -> HousingDecisionDTO:
        """
        Evaluates the household's situation and market conditions to recommend a housing action.

        Args:
            household: The current state of the household.
            market: The current state of the housing market.
            config: The simulation configuration object.

        Returns:
            A DTO representing the recommended decision.
        """
        ...
```
