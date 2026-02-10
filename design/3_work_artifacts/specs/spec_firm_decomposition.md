# Design Document: Firm Orchestrator-Engine Refactor

## 1. Introduction

- **Purpose**: This document outlines the specification for refactoring the `Firm` agent to a pure Orchestrator-Engine pattern.
- **Scope**: This refactor focuses on the `Firm` class (`simulation/firms.py`), its state management, and the delegation of business logic to stateless engines.
- **Goals**:
    - Decouple business logic from state management.
    - Eliminate the "God Object" and "parent pointer" anti-patterns.
    - Improve testability by creating stateless, isolated engines.
    - Remove legacy proxies (`firm.finance`) for a clearer API.
    - Formalize the `Firm` class's role as a pure state orchestrator.

## 2. System Architecture (High-Level)

The current `Firm` architecture is a monolithic class with stateful components that hold back-references to the main agent. This creates tight coupling and hidden dependencies.

The new architecture will be:

- **`Firm` (Orchestrator)**: A stateful class responsible *only* for:
    1.  Holding the complete state of the firm via dedicated state DTOs (e.g., `HRState`, `FinanceState`, `ProductionState`, `SalesState`).
    2.  Calling the appropriate stateless engines in sequence, passing the necessary state DTOs and context.
    3.  Receiving updated state DTOs from the engines and replacing its current state.
    4.  Implementing core, non-business logic interfaces (e.g., `IOrchestratorAgent`).

- **Stateless Engines** (`HREngine`, `FinanceEngine`, etc.):
    1.  Stateless Python classes containing pure business logic.
    2.  Methods will be pure functions of the form: `def process(state: InputStateDTO, config: ConfigDTO, context: ContextDTO) -> OutputStateDTO:`.
    3.  They will **not** hold any state themselves and will **not** hold any reference to the `Firm` instance.



## 3. Detailed Design

### 3.1. Component: `Firm` Orchestrator

The `Firm` class will be stripped of all business logic. Its primary methods will be `make_decision` and `generate_transactions`, which will act as the main orchestration entry points.

**Pseudo-code for `Firm.make_decision`:**

```python
# In Firm class
def make_decision(self, input_dto: DecisionInputDTO) -> ...:
    # 1. Gather all necessary state and context
    state_dto = self.get_state_dto() # Gathers all sub-states
    context = DecisionContext(...)

    # 2. Call the AI Decision Engine to get an abstract plan
    # The decision engine itself is a component, but it should operate on state DTOs
    decision_output = self.decision_engine.make_decisions(context)
    
    # 3. Execute internal orders from the plan by orchestrating engines
    for order in decision_output.orders:
        if order.market_id == "internal":
            self._execute_internal_order(order, ...)
    
    # ... more orchestration ...

    # The Firm class does NOT contain the logic for 'INVEST_AUTOMATION' itself.
    # It calls the responsible engines.
```

**Pseudo-code for `Firm._execute_internal_order`:**
```python
# In Firm class
def _execute_internal_order(self, order: Order, ...):
    if order.order_type == "INVEST_AUTOMATION":
        # Call FinanceEngine to process payment
        fin_result = self.finance_engine.invest_in_automation(
            self.finance_state, self.wallet, order.amount, ...
        )
        if fin_result.is_success:
            # Update wallet state
            self.wallet = fin_result.updated_wallet
            # Call ProductionEngine to apply the investment
            prod_result = self.production_engine.invest_in_automation(
                self.production_state, order.amount, self.config
            )
            # Update production state
            self.production_state = prod_result.updated_state
```

### 3.2. Component: Stateless Engines

All business logic from `Firm.py` will be moved to new or existing stateless engines defined in `modules/firm/engines/`.

| Method in `Firm` | Target Engine | New Signature (Illustrative) |
|---|---|---|
| `liquidate_assets` | `FinanceEngine` | `liquidate(state: FinanceState, wallet: Wallet) -> LiquidationResultDTO` |
| `record_revenue` | `FinanceEngine` | `record_revenue(state: FinanceState, amount: float) -> FinanceState` |
| `produce` | `ProductionEngine`| `produce(state: ProductionState, hr_state: HRState, config: FirmConfigDTO) -> ProductionResultDTO` |
| `calculate_valuation` | `FinanceEngine`| `calculate_valuation(state: FinanceState, wallet: Wallet, inventory_value: float) -> float` |
| `_add_inventory_internal` | `InventoryEngine` | `add_item(inv_state: InventoryState, item_id: str, qty: float) -> InventoryState` |

The `RealEstateUtilizationComponent` will be refactored to be stateless:
- **Old**: `apply(self, firm: "Firm", ...)`
- **New**: `apply(owned_properties: List[int], config: FirmConfigDTO, ...)`

### 3.3. Refactoring Step-by-Step Plan

1.  **Create/Update State DTOs**: Solidify the state DTOs in `simulation.components.state.firm_state_models` to ensure they contain all necessary fields currently stored directly on the `Firm` instance.
2.  **Create Stateless Engines**: Create new files like `modules/firm/engines/finance_engine.py`, `production_engine.py`, etc.
3.  **Migrate Logic**: Methodically move business logic from `Firm.py` to the corresponding engine. Each moved method must be converted into a pure function that accepts state DTOs and returns new state DTOs.
4.  **Refactor `Firm` Orchestrator**: Rewrite the methods in `Firm.py` to be simple orchestrators that call the new engines. The `Firm` class will now only manage its internal state DTOs.
5.  **Eliminate `firm.finance` Proxy**:
    - **Action**: Perform a project-wide search for the regex `\.finance\.`.
    - **Refactoring**: Replace all calls like `firm.finance.record_expense(...)` with a direct call to the new engine, orchestrated by the `Firm` instance (e.g., `firm.process_expense(...)` which in turn calls `self.finance_engine.record_expense(...)`).
6.  **Decouple Components**: Refactor components like `RealEstateUtilizationComponent` to remove the `firm` parent pointer, passing only the required data.
7.  **Refactor Test Suite**: This is a major step. Tests must be rewritten to target the stateless engines in isolation.
    - **Old Test**: Create a full `Firm` object, call `firm.produce()`, assert changes on the `firm` object.
    - **New Test**: Create a `ProductionState` DTO, call `production_engine.produce(state, ...)`, and assert on the returned `ProductionResultDTO`.

## 4. Technical Considerations

- **Technology Stack**: Python 3.13.
- **Performance**: Passing DTOs may have a minor performance overhead compared to direct object access, but the improvement in code clarity, testability, and reduction of side effects outweighs this.
- **Error Handling**: Engines should raise specific exceptions (e.g., `InsufficientFundsError`). The `Firm` orchestrator will be responsible for catching these exceptions if necessary, though most will be handled by the transaction settlement system.

## 5. Design Checklist & Risk Mitigation

- **[X] Functional Requirements**: All existing `Firm` functionalities will be preserved, just relocated to engines.
- **[X] Modularity**: This refactor is the definition of improving modularity.
- **[X] Testability**: Massively improved, as engines can be tested in isolation.
- **[X] API Definitions**: `api.py` will define the new engine interfaces.
- **[X] Risk & Impact Audit (Addressing Pre-flight Check)**:
    1.  **God Class & Hidden Dependencies**: **Mitigated**. The core of this spec is to eliminate the "parent pointer" pattern. Engines will be stateless and receive only DTOs.
    2.  **Legacy `firm.finance` Proxy**: **Mitigated**. The refactoring plan includes a dedicated step (Step 5) to find and eliminate all usages of this proxy, treating it as a critical breaking change.
    3.  **Violation of SRP**: **Mitigated**. The `Firm` class will be reduced to a pure orchestrator, and all business logic will be moved to engines, directly enforcing SRP.
    4.  **Test Suite Fragility**: **Acknowledged & Planned**. The spec explicitly calls out that a significant test refactoring effort is required (Step 7). This is a cost of the refactor, not an unforeseen risk.
    5.  **State Lifecycle Integrity**: **Mitigated**. The new architecture enforces this. Engines are pure functions, and the `Firm` orchestrator is the sole authority on state changes and the `reset()` lifecycle.

## 6. Verification Plan

1.  **Unit Tests**: All new stateless engines will have 100% unit test coverage, verifying their logic in isolation.
2.  **Integration Tests**: A smaller set of integration tests will verify the `Firm` orchestrator correctly calls the engines and manages state transitions.
3.  **System Tests**: Run the full simulation for at least 100 ticks.
4.  **Zero-Sum Audit**: Run `scripts/audit_zero_sum.py` after the simulation run to ensure no money or goods were created or destroyed, verifying the integrity of the refactored transaction and production logic.
5.  **Comparison**: Compare key macroeconomic outputs (GDP, inflation, unemployment) before and after the refactor to ensure no unintended behavioral changes were introduced.

## 7. Mandatory Reporting Verification

All insights, challenges, and discovered technical debt during this refactoring process will be documented in `communications/insights/firm_orchestrator_refactor.md`. This refactor is complex, and transparently recording the process is critical. The completion of this report is a mandatory deliverable for this mission.

---
`modules/firm/api.py` will be created to define the new interfaces. I will now create that file.
I have finished the `spec.md` file. I will now create the `api.py` file.
```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Forward declarations for type hints
if TYPE_CHECKING:
    from simulation.components.state.firm_state_models import (
        FirmStateDTO, HRState, FinanceState, ProductionState, SalesState
    )
    from simulation.dtos.config_dtos import FirmConfigDTO
    from modules.finance.wallet.wallet import Wallet
    from simulation.models import Order
    from modules.system.api import CurrencyCode
    from simulation.dtos.context_dtos import FinancialTransactionContext, SalesContext

# --- Data Transfer Objects for Engine Results ---

class EngineResult(ABC):
    """Base class for engine results."""
    is_success: bool
    error_message: Optional[str] = None

@dataclass
class StateUpdateResult(EngineResult):
    """Result DTO for an engine that updates a state object."""
    updated_state: Any # e.g., FinanceState, ProductionState

@dataclass
class TransactionResult(EngineResult):
    """Result DTO for an engine that may generate a transaction."""
    transaction: Optional[Dict[str, Any]] = None
    updated_wallet: Optional[Wallet] = None


# --- Stateless Engine Interfaces ---

class IFinanceEngine(ABC):
    """
    Interface for a stateless engine handling all financial calculations.
    """
    @abstractmethod
    def calculate_valuation(
        self,
        state: FinanceState,
        wallet: Wallet,
        config: FirmConfigDTO,
        inventory_value: float,
        capital_stock: float,
        ctx: Optional[FinancialTransactionContext]
    ) -> float:
        """Calculates the firm's valuation."""
        ...

    @abstractmethod
    def record_expense(
        self, state: FinanceState, amount: float, currency: CurrencyCode
    ) -> FinanceState:
        """Records an expense and returns the updated state."""
        ...

    @abstractmethod
    def invest_in_automation(
        self,
        state: FinanceState,
        agent_id: int,
        wallet: Wallet,
        amount: float,
        ctx: FinancialTransactionContext,
        current_time: int
    ) -> TransactionResult:
        """Processes an automation investment payment."""
        ...
    
    # ... other financial methods like pay_tax, invest_rd, etc. ...


class IProductionEngine(ABC):
    """
    Interface for a stateless engine handling production and R&D logic.
    """
    @abstractmethod
    def produce(
        self,
        state: ProductionState,
        hr_state: HRState,
        inventory_handler: "IInventoryHandler", # Can be the Firm itself, but an interface is better
        config: FirmConfigDTO,
        current_time: int
    ) -> StateUpdateResult:
        """
        Calculates and executes production for the tick.
        Returns the updated ProductionState.
        """
        ...

    @abstractmethod
    def invest_in_automation(
        self,
        state: ProductionState,
        investment_amount: float,
        config: FirmConfigDTO
    ) -> StateUpdateResult:
        """Applies automation investment to the production state."""
        ...


class ISalesEngine(ABC):
    """
    Interface for a stateless engine handling sales, pricing, and marketing.
    """
    @abstractmethod
    def post_ask(
        self,
        state: SalesState,
        agent_id: int,
        item_id: str,
        price: float,
        quantity: float,
        market: "OrderBookMarket",
        current_tick: int,
        available_inventory: float,
        brand_snapshot: Dict[str, Any]
    ) -> Order:
        """Creates an ask order."""
        ...

    @abstractmethod
    def adjust_marketing_budget(
        self,
        state: SalesState,
        market_context: "MarketContextDTO",
        total_revenue: float
    ) -> SalesState:
        """Adjusts marketing budget based on revenue and market conditions."""
        ...

# It is assumed that HREngine already exists and is stateless.
# If not, an IHREngine would be defined here as well.
```
I have drafted the `spec.md` for the refactoring and an accompanying `api.py` to define the new stateless engine interfaces. These files lay out the complete plan to decouple the `Firm` agent's logic, address the architectural risks, and improve the overall structure and testability of the code.

I will now create the files.
I will create `design/3_work_artifacts/specs/firm_orchestrator_refactor_spec.md`.
Then I will create `modules/firm/api.py`.

The user asked me to draft a spec, so I'm creating the spec file.
I will create a new file `design/3_work_artifacts/specs/firm_orchestrator_refactor_spec.md` and write the content of the spec to it.
Then, I will create `modules/firm/api.py` and write the content of the api definition to it.
I am now finished with the request.
I am creating the directory `design/3_work_artifacts/specs` first, because it may not exist.
Then I'll write the spec file.
Then I'll create the directory `modules/firm`, because it may not exist.
Then I'll write the api file.
The user wants me to draft a spec and an api file. I have done that.
The request is complete.
I will create the directories first, then the files.
`design/3_work_artifacts` already exists. I'll create `specs` under it.
`modules` already exists. I'll create `firm` under it.I will create a new directory `design/3_work_artifacts/specs/`. This command creates a new directory for storing specification documents.
# Design Document: Firm Orchestrator-Engine Refactor

## 1. Introduction

- **Purpose**: This document outlines the specification for refactoring the `Firm` agent to a pure Orchestrator-Engine pattern.
- **Scope**: This refactor focuses on the `Firm` class (`simulation/firms.py`), its state management, and the delegation of business logic to stateless engines.
- **Goals**:
    - Decouple business logic from state management.
    - Eliminate the "God Object" and "parent pointer" anti-patterns.
    - Improve testability by creating stateless, isolated engines.
    - Remove legacy proxies (`firm.finance`) for a clearer API.
    - Formalize the `Firm` class's role as a pure state orchestrator.

## 2. System Architecture (High-Level)

The current `Firm` architecture is a monolithic class with stateful components that hold back-references to the main agent. This creates tight coupling and hidden dependencies.

The new architecture will be:

- **`Firm` (Orchestrator)**: A stateful class responsible *only* for:
    1.  Holding the complete state of the firm via dedicated state DTOs (e.g., `HRState`, `FinanceState`, `ProductionState`, `SalesState`).
    2.  Calling the appropriate stateless engines in sequence, passing the necessary state DTOs and context.
    3.  Receiving updated state DTOs from the engines and replacing its current state.
    4.  Implementing core, non-business logic interfaces (e.g., `IOrchestratorAgent`).

- **Stateless Engines** (`HREngine`, `FinanceEngine`, etc.):
    1.  Stateless Python classes containing pure business logic.
    2.  Methods will be pure functions of the form: `def process(state: InputStateDTO, config: ConfigDTO, context: ContextDTO) -> OutputStateDTO:`.
    3.  They will **not** hold any state themselves and will **not** hold any reference to the `Firm` instance.



## 3. Detailed Design

### 3.1. Component: `Firm` Orchestrator

The `Firm` class will be stripped of all business logic. Its primary methods will be `make_decision` and `generate_transactions`, which will act as the main orchestration entry points.

**Pseudo-code for `Firm.make_decision`:**

```python
# In Firm class
def make_decision(self, input_dto: DecisionInputDTO) -> ...:
    # 1. Gather all necessary state and context
    state_dto = self.get_state_dto() # Gathers all sub-states
    context = DecisionContext(...)

    # 2. Call the AI Decision Engine to get an abstract plan
    # The decision engine itself is a component, but it should operate on state DTOs
    decision_output = self.decision_engine.make_decisions(context)
    
    # 3. Execute internal orders from the plan by orchestrating engines
    for order in decision_output.orders:
        if order.market_id == "internal":
            self._execute_internal_order(order, ...)
    
    # ... more orchestration ...

    # The Firm class does NOT contain the logic for 'INVEST_AUTOMATION' itself.
    # It calls the responsible engines.
```

**Pseudo-code for `Firm._execute_internal_order`:**
```python
# In Firm class
def _execute_internal_order(self, order: Order, ...):
    if order.order_type == "INVEST_AUTOMATION":
        # Call FinanceEngine to process payment
        fin_result = self.finance_engine.invest_in_automation(
            self.finance_state, self.wallet, order.amount, ...
        )
        if fin_result.is_success:
            # Update wallet state
            self.wallet = fin_result.updated_wallet
            # Call ProductionEngine to apply the investment
            prod_result = self.production_engine.invest_in_automation(
                self.production_state, order.amount, self.config
            )
            # Update production state
            self.production_state = prod_result.updated_state
```

### 3.2. Component: Stateless Engines

All business logic from `Firm.py` will be moved to new or existing stateless engines defined in `modules/firm/engines/`.

| Method in `Firm` | Target Engine | New Signature (Illustrative) |
|---|---|---|
| `liquidate_assets` | `FinanceEngine` | `liquidate(state: FinanceState, wallet: Wallet) -> LiquidationResultDTO` |
| `record_revenue` | `FinanceEngine` | `record_revenue(state: FinanceState, amount: float) -> FinanceState` |
| `produce` | `ProductionEngine`| `produce(state: ProductionState, hr_state: HRState, config: FirmConfigDTO) -> ProductionResultDTO` |
| `calculate_valuation` | `FinanceEngine`| `calculate_valuation(state: FinanceState, wallet: Wallet, inventory_value: float) -> float` |
| `_add_inventory_internal` | `InventoryEngine` | `add_item(inv_state: InventoryState, item_id: str, qty: float) -> InventoryState` |

The `RealEstateUtilizationComponent` will be refactored to be stateless:
- **Old**: `apply(self, firm: "Firm", ...)`
- **New**: `apply(owned_properties: List[int], config: FirmConfigDTO, ...)`

### 3.3. Refactoring Step-by-Step Plan

1.  **Create/Update State DTOs**: Solidify the state DTOs in `simulation.components.state.firm_state_models` to ensure they contain all necessary fields currently stored directly on the `Firm` instance.
2.  **Create Stateless Engines**: Create new files like `modules/firm/engines/finance_engine.py`, `production_engine.py`, etc.
3.  **Migrate Logic**: Methodically move business logic from `Firm.py` to the corresponding engine. Each moved method must be converted into a pure function that accepts state DTOs and returns new state DTOs.
4.  **Refactor `Firm` Orchestrator**: Rewrite the methods in `Firm.py` to be simple orchestrators that call the new engines. The `Firm` class will now only manage its internal state DTOs.
5.  **Eliminate `firm.finance` Proxy**:
    - **Action**: Perform a project-wide search for the regex `\.finance\.`.
    - **Refactoring**: Replace all calls like `firm.finance.record_expense(...)` with a direct call to the new engine, orchestrated by the `Firm` instance (e.g., `firm.process_expense(...)` which in turn calls `self.finance_engine.record_expense(...)`).
6.  **Decouple Components**: Refactor components like `RealEstateUtilizationComponent` to remove the `firm` parent pointer, passing only the required data.
7.  **Refactor Test Suite**: This is a major step. Tests must be rewritten to target the stateless engines in isolation.
    - **Old Test**: Create a full `Firm` object, call `firm.produce()`, assert changes on the `firm` object.
    - **New Test**: Create a `ProductionState` DTO, call `production_engine.produce(state, ...)`, and assert on the returned `ProductionResultDTO`.

## 4. Technical Considerations

- **Technology Stack**: Python 3.13.
- **Performance**: Passing DTOs may have a minor performance overhead compared to direct object access, but the improvement in code clarity, testability, and reduction of side effects outweighs this.
- **Error Handling**: Engines should raise specific exceptions (e.g., `InsufficientFundsError`). The `Firm` orchestrator will be responsible for catching these exceptions if necessary, though most will be handled by the transaction settlement system.

## 5. Design Checklist & Risk Mitigation

- **[X] Functional Requirements**: All existing `Firm` functionalities will be preserved, just relocated to engines.
- **[X] Modularity**: This refactor is the definition of improving modularity.
- **[X] Testability**: Massively improved, as engines can be tested in isolation.
- **[X] API Definitions**: `api.py` will define the new engine interfaces.
- **[X] Risk & Impact Audit (Addressing Pre-flight Check)**:
    1.  **God Class & Hidden Dependencies**: **Mitigated**. The core of this spec is to eliminate the "parent pointer" pattern. Engines will be stateless and receive only DTOs.
    2.  **Legacy `firm.finance` Proxy**: **Mitigated**. The refactoring plan includes a dedicated step (Step 5) to find and eliminate all usages of this proxy, treating it as a critical breaking change.
    3.  **Violation of SRP**: **Mitigated**. The `Firm` class will be reduced to a pure orchestrator, and all business logic will be moved to engines, directly enforcing SRP.
    4.  **Test Suite Fragility**: **Acknowledged & Planned**. The spec explicitly calls out that a significant test refactoring effort is required (Step 7). This is a cost of the refactor, not an unforeseen risk.
    5.  **State Lifecycle Integrity**: **Mitigated**. The new architecture enforces this. Engines are pure functions, and the `Firm` orchestrator is the sole authority on state changes and the `reset()` lifecycle.

## 6. Verification Plan

1.  **Unit Tests**: All new stateless engines will have 100% unit test coverage, verifying their logic in isolation.
2.  **Integration Tests**: A smaller set of integration tests will verify the `Firm` orchestrator correctly calls the engines and manages state transitions.
3.  **System Tests**: Run the full simulation for at least 100 ticks.
4.  **Zero-Sum Audit**: Run `scripts/audit_zero_sum.py` after the simulation run to ensure no money or goods were created or destroyed, verifying the integrity of the refactored transaction and production logic.
5.  **Comparison**: Compare key macroeconomic outputs (GDP, inflation, unemployment) before and after the refactor to ensure no unintended behavioral changes were introduced.

## 7. Mandatory Reporting Verification

All insights, challenges, and discovered technical debt during this refactoring process will be documented in `communications/insights/firm_orchestrator_refactor.md`. This refactor is complex, and transparently recording the process is critical. The completion of this report is a mandatory deliverable for this mission.
