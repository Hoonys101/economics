# Spec: Decoupling FinanceDepartment

## 1. Executive Summary & Risk Mitigation

This document outlines the technical specification for decoupling the `FinanceDepartment` from the `Firm` agent. This is a foundational refactoring effort that directly addresses the architectural risks and technical debt identified in the **Pre-flight Audit** and `ARCH_AGENTS.md`.

While contradicting the previous "inseparable unit" doctrine, this refactor is deemed necessary to enforce state isolation, improve testability, and establish a clear, data-driven contract between the `Firm` and its financial logic. The current stateful component pattern has led to hidden dependencies and complex state management, which this proposal aims to resolve.

The core mitigation strategy involves inverting control and communication flow:
1.  **Data In, Data Out**: The `FinanceDepartment` will no longer hold a reference to the `Firm`. Instead, all necessary `Firm` state will be passed in via a comprehensive `FinanceContextDTO`.
2.  **State Mutation via DTOs**: All methods that previously mutated `Firm` state will now return a `FirmStateUpdateDTO`, describing the intended change. The `Firm` is responsible for applying this update.
3.  **Transaction as Action**: All actions requiring fund transfers (investments, tax payments) will return `Transaction` objects instead of executing them directly. The `Firm`'s settlement logic will process these transactions.

This approach transforms `FinanceDepartment` into a pure, portable, and independently verifiable component.

## 2. DTO Architecture

### 2.1. `FinanceContextDTO` (Input)
This DTO aggregates all necessary read-only state from the `Firm` and the broader environment, serving as the sole input for `FinanceDepartment` methods.

```python
from typing import TypedDict, Dict, List, Optional, Deque
from modules.system.api import CurrencyCode, MarketContextDTO
from modules.finance.dtos import MultiCurrencyWalletDTO

class FirmFinancialStateDTO(TypedDict):
    """Read-only snapshot of the Firm's state needed for financial calculations."""
    id: int
    total_shares: float
    treasury_shares: float
    capital_stock: float
    dividend_rate: float
    valuation: float # last known valuation
    is_bankrupt: bool
    has_bailout_loan: bool
    total_debt: float
    # Inventory & Production
    inventory_value: float # Pre-calculated in primary currency
    last_daily_expenses: float # In primary currency
    production_target: float
    # Shareholder Info
    shareholders: List[Dict] # Structure from IShareholderRegistry
    # History
    profit_history: Deque[float] # In primary currency
    # Config values that might be dynamic
    dividend_policy: Dict # e.g., dividend rate, payout ratio

class FinanceContextDTO(TypedDict):
    """The complete context for any FinanceDepartment operation."""
    firm_state: FirmFinancialStateDTO
    wallet: MultiCurrencyWalletDTO # The firm's wallet state
    market_context: MarketContextDTO # Includes exchange rates
    current_time: int
```

### 2.2. `FirmStateUpdateDTO` (Output)
A data structure that describes a requested change to the `Firm`'s state. Fields are `Optional` to allow for partial updates.

```python
from typing import TypedDict, Optional, Dict
from modules.system.api import CurrencyCode

class FirmStateUpdateDTO(TypedDict, total=False):
    """Describes a state change for the Firm agent."""
    is_bankrupt: bool
    has_bailout_loan: bool
    total_debt: float # New total debt value
    total_shares: float # New total shares
    dividend_rate: float
    retained_earnings: float
    # Period trackers that Finance used to manage internally
    current_profit: Dict[CurrencyCode, float]
    revenue_this_turn: Dict[CurrencyCode, float]
    cost_this_turn: Dict[CurrencyCode, float]
```

### 2.3. `FinancialOperationsOutputDTO` (Output)
The consolidated output from a financial processing step, containing all generated transactions and state update requests.

```python
from typing import TypedDict, List
from simulation.models import Transaction

class FinancialOperationsOutputDTO(TypedDict):
    transactions: List[Transaction]
    state_updates: List[FirmStateUpdateDTO]
```

## 3. Modified `FinanceDepartment` Interface & Logic

The `IFinanceDepartment` in `modules/finance/api.py` will be updated. All methods will be stateless and receive the `FinanceContextDTO`.

### 3.1. Method Signature Transformation (Example)

**Before (Stateful):**
`def process_profit_distribution(self, shareholder_registry: IShareholderRegistry, government: IFinancialEntity, ...) -> List[Transaction]:`

**After (Stateless):**
`def process_profit_distribution(self, context: FinanceContextDTO, government_id: int) -> FinancialOperationsOutputDTO:`

### 3.2. Pseudo-code: `process_profit_distribution`

```python
# In the new, decoupled FinanceDepartment

def process_profit_distribution(self, context: FinanceContextDTO, government_id: int) -> FinancialOperationsOutputDTO:
    # 1. Unpack context
    firm_state = context['firm_state']
    wallet = context['wallet']
    market_context = context['market_context']
    current_time = context['current_time']
    current_profit = context['firm_state']['current_profit_clone'] # Work on a copy

    transactions = []
    state_updates = []

    # 2. Bailout Repayment Logic (Creates a transaction and a state update)
    if firm_state['has_bailout_loan'] and current_profit.get(DEFAULT_CURRENCY, 0.0) > 0:
        # ... calculation logic ...
        repayment = ...
        transactions.append(Transaction(
            buyer_id=firm_state['id'],
            seller_id=government_id,
            ...
            price=repayment
        ))
        
        # Request state change instead of mutating
        new_total_debt = firm_state['total_debt'] - repayment
        current_profit[DEFAULT_CURRENCY] -= repayment
        state_updates.append(FirmStateUpdateDTO(
            total_debt=new_total_debt,
            has_bailout_loan=(new_total_debt > 0)
        ))

    # 3. Dividend Logic (Creates transactions)
    # ... logic using firm_state['shareholders'] and current_profit ...
    for shareholder in firm_state['shareholders']:
        # ... calculation logic ...
        dividend_amount = ...
        transactions.append(Transaction(
            buyer_id=firm_state['id'],
            seller_id=shareholder['agent_id'],
            ...
            price=dividend_amount
        ))

    # 4. Create state update for profit reset
    state_updates.append(FirmStateUpdateDTO(
        current_profit={cur: 0.0 for cur in current_profit},
        # also reset revenue_this_turn, etc.
    ))

    # 5. Consolidate and return
    return FinancialOperationsOutputDTO(
        transactions=transactions,
        state_updates=state_updates
    )
```

### 3.3. Pseudo-code: `Firm` Agent Integration

```python
# In Firm.generate_transactions method

# 1. Assemble the context DTO
firm_state_dto = self.get_financial_state_snapshot() # New helper method
finance_context = FinanceContextDTO(
    firm_state=firm_state_dto,
    wallet=MultiCurrencyWalletDTO(balances=self.wallet.get_all_balances()),
    market_context=market_context,
    current_time=current_time
)

# 2. Call the stateless financial logic
# (Holding costs, maintenance, profit distribution are now consolidated)
financial_output = self.finance_component.run_end_of_tick_operations(
    finance_context, 
    government_id=government.id
)

# 3. Process the output
all_transactions.extend(financial_output['transactions'])
for update in financial_output['state_updates']:
    self.apply_state_update(update) # New helper to apply DTO changes
```

## 4. Verification & Testing Plan

1.  **New Test Suite**: A new test file, `tests/components/test_finance_department.py`, will be created. It will test the `FinanceDepartment` in complete isolation.
2.  **Mocking Strategy**:
    *   A `fixture` will provide a "golden" `FinanceContextDTO` instance representing a typical mid-game firm.
    *   Tests will call `finance_component` methods with this context and assert that the returned `FinancialOperationsOutputDTO` is correct (e.g., correct transaction amounts, correct state update values).
3.  **`Firm` Test Overhaul**: `tests/test_firms.py` will be significantly refactored. Tests related to financial outcomes will be updated to follow the new "assemble -> call -> process" flow.
4.  **Schema Enforcement**: The `FinanceContextDTO` and `FirmStateUpdateDTO` will be rigorously defined with `TypedDict` to allow static analysis with `mypy` to catch data contract violations early.

## 5. 🚨 Risk & Impact Audit (Adherence to Pre-flight Check)

-   **Architectural Doctrine**: This spec formally acknowledges the shift and documents it, superseding the old `ARCH_AGENTS.md` principle for this component. This is a deliberate, managed evolution of the architecture.
-   **State Mutation Inversion**: The `FirmStateUpdateDTO` directly implements the required inversion of control, mitigating this risk.
-   **Dependency Management**: The `FinanceContextDTO` makes all data dependencies explicit. While large, it is a clear contract that prevents hidden dependencies.
-   **Service Access**: The pattern of returning `Transaction` objects decouples the component from the live `SettlementSystem`, as required.
-   **Testability Cascade**: The verification plan explicitly budgets for the creation of a new test suite and the overhaul of existing tests, acknowledging the scale of the task.

## 6. 🚨 Mandatory Reporting Verification

Insights and technical debt addressed by this refactoring have been recorded in `communications/insights/FIN-DECOUPLE-01.md`. This deliverable satisfies the mandatory reporting requirement.

---
# API: `modules/finance/api.py`

```python
from __future__ import annotations
from typing import Protocol, List, Dict, Optional, Deque, TypedDict, Union
from collections import deque

from modules.system.api import CurrencyCode, MarketContextDTO
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, InsufficientFundsError

# =================================================================
# DTOs for Decoupled Finance Department
# =================================================================

class FirmFinancialStateDTO(TypedDict):
    """Read-only snapshot of the Firm's state needed for financial calculations."""
    id: int
    total_shares: float
    treasury_shares: float
    capital_stock: float
    dividend_rate: float
    valuation: float
    is_bankrupt: bool
    has_bailout_loan: bool
    total_debt: float
    inventory_value: float
    last_daily_expenses: float
    production_target: float
    shareholders: List[Dict]
    profit_history: Deque[float]
    # State previously internal to FinanceDept now passed in
    retained_earnings: float
    consecutive_loss_turns: int
    current_profit: Dict[CurrencyCode, float]
    revenue_this_turn: Dict[CurrencyCode, float]
    cost_this_turn: Dict[CurrencyCode, float]
    expenses_this_tick: Dict[CurrencyCode, float]


class FinanceContextDTO(TypedDict):
    """The complete context for any FinanceDepartment operation."""
    firm_state: FirmFinancialStateDTO
    wallet: MultiCurrencyWalletDTO
    market_context: MarketContextDTO
    current_time: int
    config: "FirmConfigDTO" # Forward reference


class FirmStateUpdateDTO(TypedDict, total=False):
    """Describes a state change for the Firm agent."""
    is_bankrupt: bool
    has_bailout_loan: bool
    total_debt: float
    total_shares: float
    dividend_rate: float
    # State to be updated
    retained_earnings: float
    consecutive_loss_turns: int
    current_profit: Dict[CurrencyCode, float]
    revenue_this_turn: Dict[CurrencyCode, float]
    cost_this_turn: Dict[CurrencyCode, float]
    expenses_this_tick: Dict[CurrencyCode, float]
    # Tick-level counters
    last_daily_expenses: float
    sales_volume_this_tick: float


class FinancialOperationsOutputDTO(TypedDict):
    """Consolidated output from a financial processing step."""
    transactions: List["Transaction"] # Forward reference
    orders: List["Order"] # Forward reference
    state_updates: FirmStateUpdateDTO


# =================================================================
# Decoupled Interface
# =================================================================

class IDecoupledFinanceDepartment(Protocol):
    """
    A stateless component for handling all firm financial logic.
    It receives all necessary state via DTOs and returns transactions
    and state update requests.
    """

    def run_end_of_tick_operations(
        self, context: FinanceContextDTO, government_id: int
    ) -> FinancialOperationsOutputDTO:
        """
        Consolidates all financial outflow generation and profit distribution logic.
        This single entry point replaces multiple calls like generate_financial_transactions.
        """
        ...

    def calculate_valuation(self, context: FinanceContextDTO) -> MoneyDTO:
        """Calculates the firm's total valuation in its primary currency."""
        ...

    def check_bankruptcy(self, context: FinanceContextDTO) -> Optional[FirmStateUpdateDTO]:
        """
        Checks if the firm meets bankruptcy conditions.
        Returns a state update DTO if bankruptcy should be triggered.
        """
        ...

    def check_cash_crunch(self, context: FinanceContextDTO) -> bool:
        """Checks if the firm's cash is below a critical threshold."""
        ...
    
    def trigger_emergency_liquidation(self, context: FinanceContextDTO) -> List["Order"]:
        """Generates emergency SELL orders for all inventory."""
        ...

    def get_financial_snapshot_dto(
        self, context: FinanceContextDTO
    ) -> Dict[str, Union[MoneyDTO, MultiCurrencyWalletDTO, float]]:
        """Returns a comprehensive, currency-aware snapshot."""
        ...

# =================================================================
# Legacy Interface (To be deprecated)
# =================================================================

class IFinancialEntity(Protocol):
    ...

class IShareholderRegistry(Protocol):
    ...

class IFinanceDepartment(Protocol):
    ...

```
---
# Communications Insight

File: `communications/insights/FIN-DECOUPLE-01.md`
```markdown
# Insight: Decoupling FinanceDepartment to Enforce State Purity

**TICK**: N/A (Architectural Change)
**AGENT**: System Architect
**TAGS**: #TechDebt, #Refactor, #SoC, #StateManagement

## Observation
The `FinanceDepartment` component is tightly coupled to the `Firm` agent, holding a direct parent reference (`self.firm`). This allows it to arbitrarily read and mutate the `Firm`'s state, creating hidden dependencies and violating the Separation of Concerns (SoC) principle documented in `ARCH_AGENTS.md`. This pattern makes isolated testing impossible and increases the risk of unpredictable side effects.

## Action Taken
A major refactoring has been specified to decouple `FinanceDepartment`. The new architecture mandates a stateless component that operates purely on data-in, data-out principles:
1.  **Input**: All necessary state is provided via a `FinanceContextDTO`.
2.  **Output**: All outcomes are returned as data: `Transaction` objects for actions and `FirmStateUpdateDTO` for state changes.

## Impact & Technical Debt Resolution
-   **Debt Resolved**: The "stateful component" anti-pattern is eliminated for the finance domain.
-   **Improved Testability**: `FinanceDepartment` can now be unit-tested in complete isolation, verifying its logic independently of the `Firm` agent's complex lifecycle.
-   **State Purity**: `Firm` state management is now explicit. The `Firm` agent is the sole authority for applying state changes, making the flow of data clear and traceable.
-   **Future Work**: This pattern should be considered the blueprint for decoupling other `Firm` components (HR, Production, Sales) in the future to further reduce architectural complexity.
```
