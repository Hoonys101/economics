# Technical Spec: Firm Protocol & Order Refactoring

## 1. Overview

This document outlines a critical refactoring of the `Firm` and `Household` agents. The primary goals are:
1.  **Enforce Protocol Purity**: Ensure all inventory modifications strictly adhere to the `IInventoryHandler` protocol, fixing audit violations related to direct dictionary manipulation.
2.  **Decouple Decision from Execution**: Refactor `Firm._execute_internal_order` to emit data-driven commands instead of causing direct state mutations. This improves traceability and aligns with the Purity Gate principle, while respecting the established "Stateful Component" architecture.

This refactoring addresses all violations from `report_20260207_191829_Domain_Auditor.md` and mitigates the risks identified in the pre-flight audit.

## 2. API & DTO Definitions (`modules/system/api.py`)

To support the command-based refactoring, the following DTOs will be introduced. These will be used to represent the internal decisions made by a `Firm`.

```python
# In modules/system/api.py

from typing import TypedDict, Union, List, Literal
from modules.finance.dtos import MoneyDTO

# --- Base Internal Command ---

class BaseInternalCommand(TypedDict):
    """Base for all internal agent commands."""
    command_type: str

# --- Specific Firm Commands ---

class SetProductionTargetCmd(BaseInternalCommand):
    command_type: Literal["SET_PRODUCTION_TARGET"]
    target: float

class InvestAutomationCmd(BaseInternalCommand):
    command_type: Literal["INVEST_AUTOMATION"]
    amount: MoneyDTO

class PayTaxCmd(BaseInternalCommand):
    command_type: Literal["PAY_TAX"]
    amount: MoneyDTO
    reason: str

class InvestRDCmd(BaseInternalCommand):
    command_type: Literal["INVEST_RD"]
    amount: MoneyDTO

class InvestCapexCmd(BaseInternalCommand):
    command_type: Literal["INVEST_CAPEX"]
    amount: MoneyDTO

class SetDividendRateCmd(BaseInternalCommand):
    command_type: Literal["SET_DIVIDEND_RATE"]
    rate: float

class SetPriceCmd(BaseInternalCommand):
    command_type: Literal["SET_PRICE"]
    item_id: str
    price: float

class FireEmployeeCmd(BaseInternalCommand):
    command_type: Literal["FIRE_EMPLOYEE"]
    employee_id: int
    severance_pay: float

# --- Union Type for Type Hinting ---

InternalCommand = Union[
    SetProductionTargetCmd,
    InvestAutomationCmd,
    PayTaxCmd,
    InvestRDCmd,
    InvestCapexCmd,
    SetDividendRateCmd,
    SetPriceCmd,
    FireEmployeeCmd,
]
```

## 3. `IInventoryHandler` Protocol Enforcement

The following changes will be made to ensure all inventory manipulations go through the defined protocol methods (`add_item`, `remove_item`).

### 3.1. `Firm.__init__`

The constructor will be modified to use `self.add_item` for setting up the initial inventory.

**Pseudo-code (`simulation/firms.py`)**:
```python
# Before
# if initial_inventory is not None:
#     self._inventory = initial_inventory.copy()

# After
if initial_inventory is not None:
    # Use protocol-compliant addition
    for item_id, qty in initial_inventory.items():
        # Assuming initial inventory has a default quality of 1.0
        self.add_item(item_id, qty, quality=1.0)
```

### 3.2. `Firm.liquidate_assets`

The method will be changed to iterate through the inventory and use `self.remove_item`.

**Pseudo-code (`simulation/firms.py`)**:
```python
# Before
# self._inventory.clear()

# After
# Create a list of keys to avoid modification during iteration issues
inventory_items = list(self._inventory.keys())
for item_id in inventory_items:
    quantity_to_remove = self.get_quantity(item_id)
    if quantity_to_remove > 0:
        self.remove_item(item_id, quantity_to_remove)
```

### 3.3. `Household.add_item` / `remove_item`

The `Household` agent's inventory methods will be corrected to stop direct dictionary manipulation and perform proper checks.

**Pseudo-code (`simulation/core_agents.py`)**:
```python
# In class Household:

@override
def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool:
    """[REVISED] Adds item to economic state inventory, updating quality correctly."""
    if quantity < 0:
        return False

    current_qty = self._econ_state.inventory.get(item_id, 0.0)
    current_quality = self._econ_state.inventory_quality.get(item_id, 1.0)

    total_qty = current_qty + quantity
    if total_qty > 0:
        new_avg_quality = ((current_qty * current_quality) + (quantity * quality)) / total_qty
        self._econ_state.inventory_quality[item_id] = new_avg_quality

    self._econ_state.inventory[item_id] = total_qty
    return True

@override
def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
    """[REVISED] Removes item from economic state inventory with safety checks."""
    if quantity < 0:
        return False
    current = self._econ_state.inventory.get(item_id, 0.0)
    if current < quantity:
        self.logger.warning(f"Attempted to remove {quantity} of {item_id}, but only have {current}.")
        return False

    self._econ_state.inventory[item_id] = current - quantity
    if self._econ_state.inventory[item_id] <= 1e-9:
        del self._econ_state.inventory[item_id]
        if item_id in self._econ_state.inventory_quality:
            del self._econ_state.inventory_quality[item_id]
    return True
```

## 4. Refactoring `Firm` Decision Execution

This change decouples the decision-making from the state mutation.

### 4.1. `Firm.make_decision` Update

The `make_decision` method will now return a list of `InternalCommand` DTOs alongside external market orders.

**Pseudo-code (`simulation/firms.py`)**:
```python
# In class Firm:

# Signature Change
def make_decision(...) -> tuple[list[Order], list[InternalCommand], Any]:
    # ... existing logic to generate decisions ...
    decision_output = self.decision_engine.make_decisions(context)
    # ...

    # NEW: The interceptor now returns commands instead of executing them
    internal_commands: List[InternalCommand] = []
    external_orders: List[Order] = []
    for order in decisions:
        if order.market_id == "internal":
            command = self._translate_internal_order_to_command(order)
            if command:
                internal_commands.append(command)
        else:
            external_orders.append(order)

    # ... other logic ...

    # Return the commands for later execution
    return external_orders, internal_commands, tactic
```

### 4.2. New: `_translate_internal_order_to_command`

This new private method replaces the direct execution logic of the old `_execute_internal_order`.

**Pseudo-code (`simulation/firms.py`)**:
```python
# In class Firm:

def _translate_internal_order_to_command(self, order: Order) -> Optional[InternalCommand]:
    """Translates an internal Order into a data-driven InternalCommand DTO."""
    
    def get_money_dto(o: Order) -> MoneyDTO:
        if o.monetary_amount:
            return o.monetary_amount
        # Fallback for older order types
        return MoneyDTO(amount=o.quantity, currency=DEFAULT_CURRENCY)

    if order.order_type == "SET_TARGET":
        return SetProductionTargetCmd(command_type="SET_PRODUCTION_TARGET", target=order.quantity)
    elif order.order_type == "INVEST_AUTOMATION":
        return InvestAutomationCmd(command_type="INVEST_AUTOMATION", amount=get_money_dto(order))
    elif order.order_type == "PAY_TAX":
        return PayTaxCmd(command_type="PAY_TAX", amount=get_money_dto(order), reason=order.item_id)
    # ... and so on for all other order types (INVEST_RD, SET_PRICE, FIRE, etc.)
    
    self.logger.warning(f"Unknown internal order type: {order.order_type}")
    return None
```

### 4.3. New: `_process_internal_commands` (The Command Bus)

This new method acts as the "Command Bus" that executes the commands emitted by `make_decision`. It will be called by the main simulation loop/manager at a specific point in the agent's lifecycle phase. This respects the "Stateful Component is Canon" architecture by keeping mutation logic within the `Firm`'s boundary, but cleanly separated from the initial decision.

**Pseudo-code (`simulation/firms.py`)**:
```python
# In class Firm:

def _process_internal_commands(
    self, 
    commands: List[InternalCommand], 
    government: Optional[Any], # Pass context needed for execution
    current_time: int
) -> None:
    """Executes a list of internal commands, mutating the firm's state."""
    for cmd in commands:
        cmd_type = cmd["command_type"]
        if cmd_type == "SET_PRODUCTION_TARGET":
            self.production.set_production_target(cmd['target'])
        elif cmd_type == "INVEST_AUTOMATION":
            self.production.invest_in_automation(cmd['amount']['amount'], government)
        elif cmd_type == "PAY_TAX":
            self.finance.pay_ad_hoc_tax(cmd['amount']['amount'], cmd['amount']['currency'], cmd['reason'], government, current_time)
        elif cmd_type == "INVEST_RD":
            self.production.invest_in_rd(cmd['amount']['amount'], government, current_time)
        elif cmd_type == "INVEST_CAPEX":
            self.production.invest_in_capex(cmd['amount']['amount'], government)
        elif cmd_type == "SET_DIVIDEND_RATE":
            self.finance.set_dividend_rate(cmd['rate'])
        elif cmd_type == "SET_PRICE":
            self.sales.set_price(cmd['item_id'], cmd['price'])
        elif cmd_type == "FIRE_EMPLOYEE":
            self.hr.fire_employee(cmd['employee_id'], cmd['severance_pay'])
        else:
            self.logger.error(f"Cannot process unknown internal command: {cmd_type}")

```

### 4.4. `AgentLifecycleManager` (or equivalent) modification

The simulation runner must be updated to orchestrate this new flow.

**Pseudo-code (Simulation Runner)**:
```python
# for agent in agents:
#   if isinstance(agent, Firm):
#     # 1. Make decision, which now returns commands
#     market_orders, internal_commands, tactic = agent.make_decision(...)
#
#     # 2. Add market orders to the order book
#     market.add_orders(market_orders)
#
#     # 3. NEW: Execute the internal commands immediately after decision
#     # This makes the temporal dependency explicit.
#     agent._process_internal_commands(internal_commands, government, current_time)
#
#     # 4. Continue with the rest of the tick (e.g., generate_transactions)
#     ...
```

## 5. 🚨 Risk & Impact Audit (Resolution)

*   **Architectural Compliance**: This design **complies** with `ARCH_AGENTS.md`. It does not fight the stateful component pattern. Instead, it introduces a "Command Bus" (`_process_internal_commands`) within the `Firm` agent itself, preserving the `Firm` and its `Departments` as a "single, inseparable unit" while achieving the goal of data-driven decisions.
*   **Test Impact**: **High**. This is a breaking change. All unit and integration tests that call `Firm.make_decision()` and subsequently assert on the firm's state (e.g., `firm.production_target`) **will fail and must be rewritten**. Tests must now inspect the `internal_commands` list returned by `make_decision` to validate the *intent* of the decision.
*   **Temporal Dependencies**: The risk is mitigated by making the dependency explicit. The `AgentLifecycleManager` will call `_process_internal_commands` immediately after `make_decision`. This ensures state is updated predictably before any subsequent methods in the same tick (like `generate_transactions`) are called, preserving the existing, implicit temporal contract.
*   **Circular Imports**: All file modifications will strictly preserve the `if TYPE_CHECKING:` guards to prevent breaking the existing circular dependency workarounds.

## 6. 🚨 Mandatory Reporting Verification
All insights, technical debt, and architectural trade-offs discovered during the implementation of this specification will be documented in a new file under `communications/insights/spec-refactor-firm-protocol.md`. This is a hard requirement for the completion of this task.
