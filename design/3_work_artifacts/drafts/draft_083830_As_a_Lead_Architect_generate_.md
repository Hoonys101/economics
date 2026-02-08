# Spec: Decision Engine Decoupling & DTO Standardization

## 1. Overview & Goals

This specification outlines the mandatory refactoring of the simulation's decision-making layer. The primary goals are to improve system robustness, testability, and maintainability by enforcing strict architectural boundaries.

- **Goal 1: Standardize `OrderDTO`**: Unify all market order types, including `StockOrder`, into a single, canonical `OrderDTO` to eliminate ambiguity between `side` and `order_type`.
- **Goal 2: Enforce DTO-Driven Decisions**: Decouple all decision engines (e.g., `ActionProposalEngine`) from concrete agent implementations by requiring them to operate exclusively on Data Transfer Objects (DTOs).
- **Goal 3: Eliminate Agent Object Access**: Remove all direct access to agent objects and their internal methods (e.g., `.wallet`, `.get_quantity`) from the decision layer.

This refactor directly addresses the technical debt outlined in `TDL-PH9-2-STRUCTURAL` and the critical risks identified in the pre-flight audit.

## 2. Problem Statement & Audit Findings Analysis

The current architecture suffers from critical flaws that impede development and increase the risk of bugs:

1.  **Insufficient & Inconsistent DTOs**: The existing `AgentStateDTO` is inadequate for decision-making, forcing engines to rely on raw agent objects. Key missing data includes employment status, market perceptions, and specialization.
2.  **Violations of SRP & Law of Demeter**: Decision engines contain complex logic to handle multiple, inconsistent agent data structures (e.g., different ways to access financial assets). This couples the decision logic to the internal implementation of other modules (finance, inventory), making the system brittle.
3.  **Ambiguous Data Contracts**: The coexistence of `OrderDTO` and `StockOrder`, along with the ambiguous `side` vs. `order_type` fields, creates confusion and potential for error.
4.  **Untestable Components**: The direct dependency on raw agent objects makes unit testing decision engines in isolation nearly impossible, requiring complex and fragile mocking of the entire agent state.

## 3. Proposed Architectural Changes

### 3.1. `OrderDTO` Standardization

The `OrderDTO` will be established as the single, canonical data structure for all market orders.

-   The `side` field (`"BUY"` or `"SELL"`) is the standard. The `order_type` field is deprecated and will be removed.
-   `StockOrder` will be merged into `OrderDTO`. A new mandatory `item_category` field will be introduced to differentiate order types.
-   Stock-specific information will be handled via the existing `metadata` field.

**New Canonical `OrderDTO` Structure:**

```python
class OrderDTO(TypedDict):
    """Canonical Data Transfer Object for all market orders."""
    agent_id: int | str
    side: Literal["BUY", "SELL"]
    item_id: str  # e.g., 'labor', 'basic_food', 'FIRM_1_STOCK'
    quantity: float
    price_limit: float
    market_id: str
    item_category: Literal["GOODS", "LABOR", "STOCK", "REAL_ESTATE"] # New mandatory field
    id: str # UUID
    metadata: Optional[Dict[str, Any]] # For stock firm_id, etc.
```

### 3.2. Decision Input DTO Design

To break the dependency on raw agent objects, we will introduce a comprehensive `DecisionInputDTO`. This DTO will act as the sole source of information for all decision engines, effectively creating an Anti-Corruption Layer between the simulation state and the decision logic.

This approach avoids creating a "God DTO" by composing the input from logical, granular sub-DTOs.

```python
# To be defined in modules/simulation/api.py

class AgentContextDTO(TypedDict):
    """
    Provides all necessary context about an agent for decision-making.
    This is a read-only snapshot.
    """
    agent_id: int | str
    agent_type: Literal["Household", "Firm"]
    # Financial State
    assets: float  # Single primary currency balance for simplicity
    # Employment & Production State
    is_employed: Optional[bool] # Null for Firms
    specialization: Optional[str] # Null for Households
    # Inventory State
    inventory: Dict[str, float] # item_id -> quantity
    # Cognitive State
    perceived_avg_prices: Dict[str, float] # item_id -> price

class DecisionInputDTO(TypedDict):
    """
    The complete input payload for any decision engine.
    """
    agent_context: AgentContextDTO
    # Future extension: world_context, market_context, etc.
```

### 3.3. Method Signature Refactoring

All decision engines MUST be refactored to accept the `DecisionInputDTO`.

**Example: `ActionProposalEngine`**

-   **Before:**
    ```python
    def propose_actions(self, agent: Any, current_time: int) -> List[List[Order]]: ...
    ```
-   **After:**
    ```python
    def propose_actions(self, input_dto: DecisionInputDTO, current_time: int) -> List[List[OrderDTO]]: ...
    ```

This change must be propagated to all other rule-based or AI-based decision engines.

## 4. Phased Implementation Plan

This refactor will be executed in a controlled, phased manner to manage risk and complexity.

1.  **Phase 1: DTO Definition**: Implement the new `OrderDTO`, `AgentContextDTO`, and `DecisionInputDTO` in `modules/simulation/api.py`. Mark the old `StockOrder` dataclass as deprecated.
2.  **Phase 2: Adapter Implementation**: Create a dedicated `DecisionInputAdapter` (or Factory). Its sole responsibility is to take a raw agent object (`Firm`, `Household`) and correctly populate a `DecisionInputDTO`. All complex, inconsistent state access logic (e.g., `agent.wallet.get_balance`, `getattr(agent, 'assets', ...)` ) will be encapsulated here.
3.  **Phase 3: Decision Engine Refactoring**: Modify `ActionProposalEngine` and other decision engines to use the new `propose_actions(self, input_dto: DecisionInputDTO, ...)` signature. All internal logic must be updated to read from the `input_dto` instead of a raw agent object.
4.  **Phase 4: Test Overhaul**: Rewrite all unit and integration tests for the decision engines. Test setups must now construct and pass the `DecisionInputDTO` using the `DecisionInputAdapter`. Direct mocking of agent objects in these tests is strictly forbidden.
5.  **Phase 5: Deprecation & Cleanup**: Once all call sites are updated, remove the deprecated `StockOrder` class and any other temporary compatibility shims.

## 5. Verification & Mocking Strategy

-   **Test Breakage is Expected**: Acknowledged high risk of test breakage. The "Test Overhaul" phase is a mandatory part of this work.
-   **DTO-Centric Fixtures**: `pytest` fixtures must be created to provide realistic `DecisionInputDTO` instances for testing. These fixtures should leverage the new `DecisionInputAdapter` and existing "Golden Data" loaders (`scripts/fixture_harvester.py`) to ensure data integrity.
-   **Prohibition of Agent Mocking**: For any test targeting a decision engine, mocking of raw `Household` or `Firm` objects is no longer permitted. Tests must validate the logic based on the DTO contract.

## 6. Risk & Impact Audit

-   **Technical Risk**: **High**. The primary risk lies in the complexity of the `DecisionInputAdapter`. Incorrectly translating agent state into the DTO will lead to subtle bugs. This risk is mitigated by the phased approach and a dedicated test overhaul.
-   **Test Impact**: **Critical**. A complete rewrite of tests for the entire decision layer is required. This is a significant but necessary cost to pay down technical debt.
-   **Scope Creep**: **Medium**. The scope is well-defined but connects to many parts of the system. Sticking to the phased plan is essential. The `DecisionInputAdapter` serves as a firebreak, preventing the need for an immediate, system-wide agent refactor.
-   **Architectural Precedent**: This refactor establishes a crucial "DTO-in, DTO-out" pattern for simulation components. Its success is vital for future modularity and the long-term health of the codebase.

## 7. Mandatory Reporting Verification

All insights, challenges, or newly discovered technical debt encountered during this refactoring process will be logged in a dedicated report file under `communications/insights/refactor-decision-engine-decoupling.md`. This is a hard requirement for the completion of the mission.

---
# API Changes: `modules/simulation/api.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Protocol, TypedDict, Any, List, Dict, Optional,
    TYPE_CHECKING, runtime_checkable, Literal
)
import logging

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.systems.api import IRegistry
    from modules.finance.api import IBankService
    from simulation.interfaces.market_interface import IMarket
    from modules.housing.api import IHousingService
    from modules.memory.api import MemoryV2Interface
    from modules.system.api import CurrencyCode

# --- NEW/UPDATED DTOs ---

class OrderDTO(TypedDict):
    """
    Canonical Data Transfer Object for all market orders.
    'order_type' is deprecated in favor of 'side' and 'item_category'.
    """
    agent_id: int | str
    side: Literal["BUY", "SELL"]
    item_id: str  # e.g., 'labor', 'basic_food', 'FIRM_1_STOCK'
    quantity: float
    price_limit: float
    market_id: str
    item_category: Literal["GOODS", "LABOR", "STOCK", "REAL_ESTATE"]
    id: str  # Unique Order ID (e.g., from uuid)
    metadata: Optional[Dict[str, Any]] # e.g., {'firm_id': 1} for stock orders


class AgentContextDTO(TypedDict):
    """
    Provides a read-only snapshot of all necessary agent context for decision-making.
    This DTO is designed to decouple decision engines from agent implementations.
    """
    agent_id: int | str
    agent_type: Literal["Household", "Firm"]
    
    # Financial State (simplified to primary currency for decision logic)
    assets: float
    
    # Employment & Production State
    is_employed: Optional[bool]  # Applicable to Households
    specialization: Optional[str]  # Applicable to Firms
    
    # Inventory State
    inventory: Dict[str, float]  # Key: item_id, Value: quantity
    
    # Cognitive State / Market Perception
    perceived_avg_prices: Dict[str, float] # Key: item_id, Value: price


class DecisionInputDTO(TypedDict):
    """
    The complete, standardized input payload for any decision engine.
    """
    agent_context: AgentContextDTO
    # This can be extended with world_context, market_context etc. in the future.


# --- EXISTING DTOs (for reference, unchanged unless specified) ---

@dataclass
class AgentCoreConfigDTO:
    """Defines the immutable, core properties of an agent."""
    id: int
    value_orientation: str
    initial_needs: Dict[str, float]
    name: str
    logger: logging.Logger
    memory_interface: Optional["MemoryV2Interface"]

@dataclass
class AgentStateDTO:
    """A snapshot of an agent's mutable state."""
    assets: Dict[CurrencyCode, float]
    inventory: Dict[str, float]
    is_active: bool

@dataclass
class DecisionDTO:
    """Represents a decision made by an engine, containing a list of proposed orders."""
    actions: list[OrderDTO] # Changed to use the new canonical OrderDTO

class ShockConfigDTO(TypedDict):
    """Configuration for the economic shock."""
    shock_start_tick: int
    shock_end_tick: int
    tfp_multiplier: float
    baseline_tfp: float

@dataclass
class EconomicIndicatorsDTO:
    """Snapshot of key market indicators for analysis modules."""
    gdp: float
    cpi: float

@dataclass
class SystemStateDTO:
    """Internal system flags and states for observation."""
    is_circuit_breaker_active: bool
    bank_total_reserves: float
    bank_total_deposits: float
    fiscal_policy_last_activation_tick: int
    central_bank_base_rate: float

@dataclass(frozen=True)
class HouseholdSnapshotDTO:
    """Read-only snapshot of a household's financial state."""
    household_id: str
    cash: float
    income: float
    credit_score: float
    existing_debt: float
    assets_value: float


# --- PROTOCOLS (Unchanged) ---
# ... (existing protocols remain the same)
```
