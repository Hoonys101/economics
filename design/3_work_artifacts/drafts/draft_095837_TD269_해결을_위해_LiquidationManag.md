# Design Spec: Liquidation Manager Refactoring (TD-269)

## 1. Introduction

- **Purpose**: This document outlines the design for refactoring the `LiquidationManager` to resolve technical debt `TD-269`.
- **Scope**: The refactoring will decouple `LiquidationManager` from the internal implementation of `Firm` by introducing a formal protocol, `ILiquidatable`. This will remove dependencies on legacy attributes (`firm.finance`) and fragile object graph traversal.
- **Goal**: The primary success metric is the successful execution of the `audit_zero_sum.py` verification script, which currently fails due to this legacy dependency.

## 2. System Architecture (High-Level)

The current architecture suffers from tight coupling, where the `LiquidationManager` knows too much about the internal structure of the `Firm` agent.

**Before:**
`LiquidationManager` -> `Firm` (direct access to `hr_service`, `tax_service`, `decision_engine.loan_market`, `state.households`)

**After:**
`LiquidationManager` -> `ILiquidatable` (Interface) <- `Firm`

The `LiquidationManager` will only interact with agents through the `ILiquidatable` protocol, making it agnostic to the agent's internal implementation. The `Firm` will be responsible for implementing this protocol and providing the necessary data.

## 3. Detailed Design

### 3.1. Component: `ILiquidatable` Protocol (New)

A new, comprehensive protocol will be defined to serve as the contract for any agent that can be liquidated.

**File Location:** `modules/finance/api.py`

```python
# In modules/common/dtos.py
class Claim(TypedDict):
    creditor_id: AgentId
    amount: float
    tier: int # 1: Employees, 2: Secured Debt, 3: Taxes, 4: Unsecured
    description: str

class EquityStake(TypedDict):
    shareholder_id: AgentId
    ratio: float # Ownership ratio (0.0 to 1.0)

# In modules/finance/api.py
class ILiquidatable(Protocol):
    """
    An interface for any entity that can undergo a formal liquidation process.
    Provides all necessary financial claims and asset information to a liquidator.
    """
    id: AgentId

    def liquidate_assets(self, current_tick: int) -> Dict[CurrencyCode, float]:
        """
        Performs internal write-offs of non-cash assets (inventory, capital)
        and returns a dictionary of all remaining cash-equivalent assets by currency.
        """
        ...

    def get_all_claims(self, ctx: LiquidationContext) -> List[Claim]:
        """
        Aggregates all non-equity claims (HR, Tax, Debt) against the entity.
        """
        ...

    def get_equity_stakes(self, ctx: LiquidationContext) -> List[EquityStake]:
        """
        Returns a list of all shareholders and their proportional stake for Tier 5 distribution.
        """
        ...
```

**New DTOs:**

-   `LiquidationContext`: A context object to pass necessary services (`IHRService`, `ITaxService`, `IShareholderRegistry`) to the `ILiquidatable` agent, avoiding the need for the agent to permanently store them.
    ```python
    # In modules/finance/dtos.py
    @dataclass
    class LiquidationContext:
        current_tick: int
        hr_service: Optional[IHRService] = None
        tax_service: Optional[ITaxService] = None
        shareholder_registry: Optional[IShareholderRegistry] = None
    ```

### 3.2. Component: `Firm` Agent (Update)

The `Firm` agent will implement the `ILiquidatable` protocol.

**File Location:** `simulation/firms.py`

```python
# class Firm(... ILiquidatable ...):

    def get_all_claims(self, ctx: LiquidationContext) -> List[Claim]:
        """
        Implements ILiquidatable.get_all_claims.
        Delegates to specialized helpers to gather all claims.
        """
        all_claims: List[Claim] = []

        # 1. Get HR Claims (Tier 1)
        if ctx.hr_service:
            employee_claims = ctx.hr_service.calculate_liquidation_employee_claims(self, ctx.current_tick)
            all_claims.extend(employee_claims)

        # 2. Get Tax Claims (Tier 3)
        if ctx.tax_service:
            tax_claims = ctx.tax_service.calculate_liquidation_tax_claims(self)
            all_claims.extend(tax_claims)
            
        # 3. Get Secured Debt Claims (Tier 2)
        # Abstracts away knowledge of LoanMarket
        total_debt = self.finance_state.total_debt
        bank_agent_id = "BANK_UNKNOWN" # Default
        if self.decision_engine.loan_market and self.decision_engine.loan_market.bank:
            bank_agent_id = self.decision_engine.loan_market.bank.id

        if total_debt > 0:
            all_claims.append(Claim(
                creditor_id=bank_agent_id,
                amount=total_debt,
                tier=2,
                description="Secured Loan"
            ))
            
        return all_claims

    def get_equity_stakes(self, ctx: LiquidationContext) -> List[EquityStake]:
        """
        Implements ILiquidatable.get_equity_stakes.
        Uses the Shareholder Registry to get ownership data.
        """
        if not ctx.shareholder_registry:
            return []

        shareholders = ctx.shareholder_registry.get_shareholders(self.id)
        outstanding_shares = self.total_shares - self.treasury_shares
        
        if outstanding_shares <= 0:
            return []

        return [
            EquityStake(shareholder_id=sh_id, ratio=sh_qty / outstanding_shares)
            for sh_id, sh_qty in shareholders.items()
        ]

```

### 3.3. Component: `LiquidationManager` (Refactor)

The manager will be simplified to operate solely on the `ILiquidatable` protocol.

**File Location:** `simulation/systems/liquidation_manager.py`

**`__init__` (Before):**
```python
def __init__(self,
             settlement_system: ISettlementSystem,
             hr_service: IHRService,
             tax_service: ITaxService,
             agent_registry: IAgentRegistry,
             public_manager: Optional[IAssetRecoverySystem] = None):
    # ... stores all services
```

**`__init__` (After):**
```python
def __init__(self,
             settlement_system: ISettlementSystem,
             agent_registry: IAgentRegistry,
             shareholder_registry: IShareholderRegistry, # New
             hr_service: IHRService, # Still needed for context
             tax_service: ITaxService, # Still needed for context
             public_manager: Optional[IAssetRecoverySystem] = None):
    self.settlement_system = settlement_system
    self.agent_registry = agent_registry
    self.shareholder_registry = shareholder_registry
    self.hr_service = hr_service
    self.tax_service = tax_service
    self.public_manager = public_manager
    # ...
```

**`initiate_liquidation` (Refactored Pseudo-code):**
```python
def initiate_liquidation(self, agent: ILiquidatable, state: SimulationState) -> None:
    # No more hasattr checks for 'finance'

    # 0. Asset Sell-off
    for handler in self.handlers:
        handler.liquidate(agent, state) # Pass protocol object

    # 1. Finalize asset liquidation and get available cash
    all_assets_dict = agent.liquidate_assets(state.time)
    available_cash = all_assets_dict.get(DEFAULT_CURRENCY, 0.0)
    other_assets = {k: v for k, v in all_assets_dict.items() if k != DEFAULT_CURRENCY}

    # 2. Build Liquidation Context
    context = LiquidationContext(
        current_tick=state.time,
        hr_service=self.hr_service,
        tax_service=self.tax_service,
        shareholder_registry=self.shareholder_registry
    )

    # 3. Get all claims via the protocol
    all_claims = agent.get_all_claims(context)

    # 4. Execute Waterfall
    self.execute_waterfall(agent, all_claims, available_cash, state, other_assets)
```

**`execute_waterfall` (Refactored Pseudo-code for Tier 5):**
```python
# ... (Tier 1-4 logic is largely unchanged) ...

# --- Tier 5: Equity ---
if remaining_cash > 0 or other_assets:
    # Get equity stakes via protocol, not global state
    context = LiquidationContext(current_tick=state.time, shareholder_registry=self.shareholder_registry)
    equity_stakes = firm.get_equity_stakes(context) # 'firm' is the ILiquidatable agent

    for stake in equity_stakes:
        shareholder = self.agent_registry.get_agent(stake['shareholder_id'])
        if shareholder:
            # Distribute primary currency
            distribution = remaining_cash * stake['ratio']
            self.settlement_system.transfer(firm, shareholder, distribution, ...)

            # Distribute foreign currencies
            for cur, amount in other_assets.items():
                dist_amount = amount * stake['ratio']
                self.settlement_system.transfer(firm, shareholder, dist_amount, ..., currency=cur)
```

### 3.4. Component: `ILiquidationHandler` (Update)

The sub-handler interface must be updated to accept the protocol.

**File Location:** `simulation/systems/liquidation_handlers.py`

**`ILiquidationHandler.liquidate` (Before):**
`def liquidate(self, firm: Firm, state: SimulationState) -> None:`

**`ILiquidationHandler.liquidate` (After):**
`def liquidate(self, agent: ILiquidatable, state: SimulationState) -> None:`

## 4. Verification Plan

1.  **Unit Tests**: Update unit tests for `LiquidationManager`. Instead of creating a complex `Firm` object, a mock object implementing the `ILiquidatable` protocol will be used. This verifies the decoupling.
2.  **Integration Test**: The `audit_zero_sum.py` script serves as the primary integration test. The script will be updated to correctly initialize the refactored `LiquidationManager`.
3.  **Success Criteria**: The `audit_zero_sum.py` script runs to completion without `AttributeError` or "missing finance component" errors related to `LiquidationManager`.

## 5. Mocking & Golden Data

-   This refactoring improves testability by allowing `LiquidationManager` to be tested with a simple mock that implements `ILiquidatable`, rather than a fully instantiated `Firm`.
-   No changes to Golden Data fixtures (`golden_households`, `golden_firms`) are required by this change.

## 6. Risk & Impact Audit (Addressing Pre-flight Findings)

-   **[ADDRESSED] Risk 1 (Deep Coupling for Debt Discovery)**: The `get_all_claims` method on the `ILiquidatable` protocol abstracts away how debt information is discovered. `LiquidationManager` no longer traverses `firm.decision_engine`.
-   **[ADDRESSED] Risk 2 (Global State Dependency for Equity Distribution)**: The new `get_equity_stakes` protocol method, which uses an injected `IShareholderRegistry` via `LiquidationContext`, removes the need for `LiquidationManager` to scan the global `state` object.
-   **[ADDRESSED] Risk 3 (Ambiguous Financial Protocol)**: The new, explicit `ILiquidatable` protocol is created, providing a single, comprehensive interface for all data required during a liquidation waterfall.
-   **[ADDRESSED] Risk 4 (Legacy Dependencies in Sub-Systems)**: The `ILiquidationHandler.liquidate` method signature is changed to accept an `ILiquidatable` object, ensuring that the protocol-based approach is enforced in all sub-handlers.

## 7. Mandatory Reporting Verification

An insight report will be generated and saved to `communications/insights/TD-269_Liquidation_Refactor_Insight.md`. The key insight is that protocol-based design is crucial for system robustness. The initial `AttributeError` was a symptom of a deeper Law of Demeter violation, and resolving it with a proper interface (`ILiquidatable`) rather than a simple patch repays the technical debt and prevents future fragility.

---

# API Definition: `modules/finance/api.py`

```python
from __future__ import annotations
from typing import List, Dict, Optional, Protocol, TypedDict, TYPE_CHECKING
from dataclasses import dataclass

# Ensure AgentId and CurrencyCode are imported from a central location like modules.system.api
from modules.system.api import AgentId, CurrencyCode 

if TYPE_CHECKING:
    from modules.hr.api import IHRService
    from modules.finance.api import ITaxService, IShareholderRegistry

# DTOs
# Placed in a central DTO file like modules/common/dtos.py in the actual implementation
class Claim(TypedDict):
    """Represents a financial claim during a liquidation waterfall."""
    creditor_id: AgentId
    amount: float
    tier: int # 1: Employees, 2: Secured Debt, 3: Taxes, 4: Unsecured
    description: str

class EquityStake(TypedDict):
    """Represents a shareholder's stake for Tier 5 distribution."""
    shareholder_id: AgentId
    ratio: float # Proportional ownership, e.g., 0.1 for 10%

# Context Object for providing services without permanent storage on the agent
# To be placed in modules/finance/dtos.py
@dataclass
class LiquidationContext:
    """Context object to supply necessary services for claim calculation."""
    current_tick: int
    hr_service: Optional[IHRService] = None
    tax_service: Optional[ITaxService] = None
    shareholder_registry: Optional[IShareholderRegistry] = None


# Protocols
class ILiquidatable(Protocol):
    """
    An interface for any entity that can undergo a formal liquidation process.
    Provides all necessary financial claims and asset information to a liquidator.
    """
    id: AgentId

    def liquidate_assets(self, current_tick: int) -> Dict[CurrencyCode, float]:
        """
        Performs internal write-offs of non-cash assets (inventory, capital)
        and returns a dictionary of all remaining cash-equivalent assets by currency.
        This signals the final step before cash distribution begins.
        """
        ...

    def get_all_claims(self, ctx: LiquidationContext) -> List[Claim]:
        """
        Aggregates all non-equity claims (HR, Tax, Debt) against the entity.
        The implementation is responsible for determining the amounts and creditors.
        """
        ...

    def get_equity_stakes(self, ctx: LiquidationContext) -> List[EquityStake]:
        """
        Returns a list of all shareholders and their proportional stake for Tier 5 distribution.
        An empty list signifies no equity holders.
        """
        ...
```

---

# API Definition: `simulation/systems/liquidation_handlers.py` (Update)

```python
from __future__ import annotations
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    # The new protocol is imported
    from modules.finance.api import ILiquidatable

class ILiquidationHandler(Protocol):
    """
    Interface for handling specific asset liquidation tasks (e.g., selling off inventory).
    """

    def liquidate(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Executes a specific part of the asset liquidation process.
        
        Args:
            agent: The liquidatable entity, compliant with the ILiquidatable protocol.
            state: The current simulation state for context.
        """
        ...
```
