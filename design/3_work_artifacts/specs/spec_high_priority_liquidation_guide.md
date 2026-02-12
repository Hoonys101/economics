# Implementation Spec: Structural Integrity & Protocol Enforcement
**Mission ID**: `PH14-INTEGRITY-SWEEP`
**Author**: Gemini Scribe
**Recipient**: Jules (Lead Developer)
**Date**: 2026-02-12

---

## 1. Overview
This specification details the implementation plan to resolve four critical technical debts identified in the `TECH_DEBT_LEDGER.md`. The focus is on reinforcing architectural purity, hardening financial protocols, and eliminating legacy interfaces. Successful completion of this mission is paramount for system stability and future development velocity.

## 2. Risk & Impact Audit (Pre-Implementation)

-   **`TD-AGENT-STATE-INVFIRM` (Serialization)**
    -   **Risk**: High. Modifying `AgentStateDTO` and `load_state` logic directly impacts the simulation's core save/load functionality. Incorrect implementation will lead to data corruption or loss on restart.
    -   **Mitigation**: The `Testing & Verification Strategy` for this module is non-negotiable. A full round-trip (save -> load -> verify) test must be created.
-   **`TD-QE-MISSING` (Finance)**
    -   **Risk**: Medium. The logic modifies a core economic lever (QE). The main risk is violating the Financial SSoT by attempting direct balance manipulation.
    -   **Mitigation**: The implementation **must** use `SettlementSystem.transfer` exclusively. The selected buyer agent handle (not ID) must be passed correctly.
-   **`TD-ENFORCE-NONE` (Shield Decorator)**
    -   **Risk**: Low (implementation), Medium (performance). The use of `inspect.stack()` can introduce significant overhead.
    -   **Mitigation**: The decorator must be designed to be disabled in production builds via a configuration flag or environment variable, as detailed in the spec.
-   **`TD-ARCH-LEAK-PROTI` (Interface Retirement)**
    -   **Risk**: Medium. This is a wide-ranging refactoring task. The risk lies in missing a usage site, leading to runtime errors or retaining legacy code paths.
    -   **Mitigation**: A systematic, file-by-file search-and-replace is required. All related unit tests for modified components must be run.

---

## 3. Module 1: `AgentStateDTO` Multi-Inventory Serialization
**Addresses**: `TD-AGENT-STATE-INVFIRM`

### 3.1. API & DTO Specification (`modules/common/dtos.py`)

The `AgentStateDTO` will be updated to support a dictionary of inventories, where each key is a named slot (e.g., "MAIN", "INPUT").

```python
# In a relevant DTOs file, e.g., modules/inventory/api.py or a common DTOs file

from typing import Dict, List
from pydantic import BaseModel, Field

class ItemDTO(BaseModel):
    name: str
    quantity: float
    quality: float = 100.0
    # ... other item attributes

class InventorySlotDTO(BaseModel):
    items: List[ItemDTO] = Field(default_factory=list)
    # ... other slot-specific attributes like capacity

# In modules/common/dtos.py (or agent-specific DTO file)

class AgentStateDTO(BaseModel):
    # ... existing fields like agent_id, class_name, balance_pennies ...

    # NEW: Replace single inventory with a dictionary of inventory slots
    inventories: Dict[str, InventorySlotDTO] = Field(default_factory=dict)

    # DEPRECATED:
    # inventory: List[ItemDTO] = Field(default_factory=list) # To be removed
```

### 3.2. Implementation: Firm `load_state` & `get_state` (Pseudo-code)

The `Firm` orchestrator will be responsible for packing and unpacking the new `inventories` structure. This avoids adding more logic to the already bloated agent class.

```python
# In modules/firm/orchestrator.py (or equivalent Firm class)

from modules.inventory.manager import InventoryManager # Assumes an inventory manager component

class Firm:
    def __init__(self, ...):
        # The firm now has an inventory manager that handles multiple named slots
        self.inventory_manager = InventoryManager(slots=["MAIN", "INPUT"])
        # ...

    def get_state(self) -> AgentStateDTO:
        """Packs the firm's current state into a DTO, including all inventory slots."""
        # ... pack other agent data ...

        inventory_dtos: Dict[str, InventorySlotDTO] = {}
        for slot_name in self.inventory_manager.get_slot_names():
            slot = self.inventory_manager.get_slot(slot_name)
            inventory_dtos[slot_name] = slot.to_dto() # Assuming slot object has a to_dto method

        return AgentStateDTO(
            # ... other fields ...
            inventories=inventory_dtos
        )

    def load_state(self, state: AgentStateDTO):
        """Loads state from a DTO, populating all inventory slots."""
        # ... load other agent data ...

        if not hasattr(self, 'inventory_manager'):
            self.inventory_manager = InventoryManager(slots=["MAIN", "INPUT"])

        # Unpack the new `inventories` structure
        for slot_name, slot_dto in state.inventories.items():
            # Get or create the inventory slot on the agent
            target_slot = self.inventory_manager.get_or_create_slot(slot_name)

            # Clear existing items and load from DTO
            target_slot.from_dto(slot_dto) # Assuming slot object has a from_dto method
```

### 3.3. Testing & Verification Strategy

1.  **Create Test**: Implement `tests/system/test_serialization.py::test_firm_multi_inventory_save_load`.
2.  **Logic**:
    *   Instantiate a `Firm`.
    *   Add items to both its "MAIN" and "INPUT" inventory slots.
    *   Call `firm.get_state()` to get the `AgentStateDTO`.
    *   Instantiate a *new* `Firm` object.
    *   Call `new_firm.load_state()` with the DTO from the first firm.
    *   Assert that the "MAIN" and "INPUT" inventories of `new_firm` are identical to the original firm's inventories.

---

## 4. Module 2: Quantitative Easing (QE) Logic in `FinanceSystem`
**Addresses**: `TD-QE-MISSING`, `TDL-031`

### 4.1. Implementation: `issue_treasury_bonds` (Pseudo-code)

The logic will be inserted into `FinanceSystem.issue_treasury_bonds` to dynamically select the bond buyer.

```python
# In modules/finance/system.py

class FinanceSystem(IFinanceSystem):

    def issue_treasury_bonds(self, amount: int, current_tick: int) -> Tuple[List[BondDTO], List[Transaction]]:
        """
        Issues new treasury bonds. Includes QE logic to select the buyer.
        """
        # Sync SSoT (already present)
        self._sync_ledger_balances()

        # --- BEGIN NEW QE LOGIC ---

        # 1. Get QE Trigger Data
        debt_to_gdp_ratio = self.fiscal_monitor.get_debt_to_gdp() # Assumes fiscal monitor provides this
        qe_threshold = self.config_module.get("economy_params.QE_DEBT_TO_GDP_THRESHOLD", 1.5)

        # 2. Select Buyer Agent Handle
        if debt_to_gdp_ratio > qe_threshold:
            # QE is active: Central Bank is the buyer
            buyer_agent = self.central_bank
            logger.info(f"QE_ACTIVE | Debt/GDP ({debt_to_gdp_ratio:.2f}) > threshold ({qe_threshold}). Buyer is CentralBank.")
        else:
            # Normal operations: Primary commercial bank is the buyer
            buyer_agent = self.bank
            logger.info(f"QE_INACTIVE | Debt/GDP ({debt_to_gdp_ratio:.2f}) <= threshold ({qe_threshold}). Buyer is Bank.")

        # --- END NEW QE LOGIC ---

        # The rest of the function remains largely the same, but uses the dynamic `buyer_agent`
        buyer_id = buyer_agent.id

        # Check funds in SettlementSystem (SSoT), not the local ledger
        buyer_balance = self.settlement_system.get_balance(buyer_id, DEFAULT_CURRENCY)

        if buyer_balance < amount:
            logger.warning(f"BOND_ISSUANCE_FAILED | Buyer {buyer_id} has insufficient funds: {buyer_balance} < {amount}")
            return [], []

        # Execute Transfer via SettlementSystem using the selected agent handle
        if self.settlement_system:
            seller_agent = self.government
            success = self.settlement_system.transfer(
                buyer_agent,   # Use the dynamically selected agent object
                seller_agent,
                amount,
                memo=f"bond_purchase_{bond_id}",
                currency=DEFAULT_CURRENCY
            )
            # ... rest of the logic ...
        # ...
```

### 4.2. Testing & Verification Strategy

1.  **Modify Test**: Update `tests/finance/test_finance_system.py::test_qe_bond_issuance`.
2.  **Scenario 1 (QE Inactive)**:
    *   Mock `fiscal_monitor.get_debt_to_gdp` to return `1.0`.
    *   Call `issue_treasury_bonds`.
    *   Assert that `settlement_system.transfer` was called with `self.bank` as the `buyer_agent`.
3.  **Scenario 2 (QE Active)**:
    *   Mock `fiscal_monitor.get_debt_to_gdp` to return `2.0`.
    *   Call `issue_treasury_bonds`.
    *   Assert that `settlement_system.transfer` was called with `self.central_bank` as the `buyer_agent`.

---

## 5. Module 3: `@enforce_purity` Runtime Protocol Shield
**Addresses**: `TD-ENFORCE-NONE`

### 5.1. API & Decorator Specification (`modules/common/protocol.py`)

A new file for housing architectural enforcement tools.

```python
# In modules/common/protocol.py

import inspect
import os
from functools import wraps

# Whitelist of modules allowed to call protected financial methods.
# Using root-relative paths for robustness.
AUTHORIZED_MODULES = [
    "modules/finance/",
    "modules/governance/",
    "modules/government/",
    "modules/simulation/systems/lifecycle.py", # Example of a specific file
]

# Controlled by environment variable for performance management.
IS_PURITY_CHECK_ENABLED = os.environ.get("ENABLE_PURITY_CHECKS", "false").lower() == "true"

class ProtocolViolationError(PermissionError):
    """Raised when a restricted method is called from an unauthorized module."""
    pass

def enforce_purity(allowed_modules: list = AUTHORIZED_MODULES):
    """
    Decorator that prevents unauthorized modules from calling the decorated method.
    Checks the caller's file path against a whitelist.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not IS_PURITY_CHECK_ENABLED:
                return func(*args, **kwargs)

            # Get the frame of the caller (stack[1] is the caller of this wrapper)
            try:
                caller_frame = inspect.stack()[1]
                caller_filepath = os.path.abspath(caller_frame.filename)

                # Normalize project root for consistent checks
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
                relative_caller_path = os.path.relpath(caller_filepath, project_root).replace('\\', '/') + '/'

                # Check if the caller's module is in the authorized list
                is_authorized = any(relative_caller_path.startswith(mod) for mod in allowed_modules)

                if not is_authorized:
                    raise ProtocolViolationError(
                        f"Unauthorized call to '{func.__name__}' from module '{relative_caller_path}'. "
                        f"This method is protected."
                    )
            finally:
                # Ensure the frame is deleted to prevent reference cycles
                del caller_frame

            return func(*args, **kwargs)
        return wrapper
    return decorator

```

### 5.2. Usage Example

Apply the decorator to a critical SSoT method.

```python
# In modules/finance/settlement.py

from modules.common.protocol import enforce_purity

class SettlementSystem:

    @enforce_purity()
    def transfer(self, buyer, seller, amount, memo, currency):
        # ... core transfer logic ...
```

### 5.3. Testing & Verification Strategy

1.  **Create Test File**: `tests/common/test_protocol.py`.
2.  **Test 1 (Authorized Call)**:
    *   Create a dummy function inside the test file (which is not in the whitelist).
    *   Have it call a decorated function.
    *   Set `ENABLE_PURITY_CHECKS=true`.
    *   Assert that `ProtocolViolationError` is raised.
3.  **Test 2 (Unauthorized Call)**:
    *   This is harder. One way is to use `exec` to simulate a call from a whitelisted module path, or place a helper file in an authorized directory.
    *   Assert that the decorated function executes without raising an error.
4.  **Test 3 (Disabled)**:
    *   Set `ENABLE_PURITY_CHECKS=false`.
    *   Assert that an unauthorized call succeeds without raising an error.

---

## 6. Module 4: Migration Plan for `IFinancialEntity`
**Addresses**: `TD-ARCH-LEAK-PROTI`

### 6.1. Problem Statement

The `IFinancialEntity` interface is a leaky abstraction that encourages direct interaction with agent objects, bypassing the Financial SSoT (`SettlementSystem`). It also contains deprecated methods (`deposit`/`withdraw`) that now raise errors.

### 6.2. Migration Strategy

The core principle is to **replace interaction with the agent with interaction with the system that governs the agent's state.**

| Old Pattern (`IFinancialEntity`) | New Pattern (SSoT Compliant) | Rationale |
| :--- | :--- | :--- |
| `entity.deposit(amount)` | `settlement_system.transfer(source, entity, amount, ...)` | Enforces SSoT. All transfers are explicit and managed by the central ledger. |
| `entity.withdraw(amount)` | `settlement_system.transfer(entity, destination, amount, ...)` | Enforces SSoT. |
| `balance = entity.get_balance()` | `balance = settlement_system.get_balance(entity.id)` | State is queried from the SSoT, not the agent's potentially stale internal state. |
| `if isinstance(obj, IFinancialEntity):` | `if hasattr(obj, 'agent_id') and settlement_system.is_registered(obj.id):` or use a new marker interface like `IFinancialAgent` if needed for polymorphism. | Type checks should be based on participation in the financial system, not a leaky interface. |

### 6.3. Action Plan

1.  **Find Usages**: Use `ripgrep` to find all instances of `IFinancialEntity`.
    ```bash
    rg "IFinancialEntity"
    ```
2.  **Refactor (Before/After Pseudo-code)**:

    **Before:**
    ```python
    # In some random module
    def pay_dividend(firm: IFinancialEntity, shareholder: IFinancialEntity, amount: int):
        if firm.get_balance() >= amount:
            firm.withdraw(amount)
            shareholder.deposit(amount)
            # This is a critical SSoT violation
    ```

    **After:**
    ```python
    # In a financial or governance module
    def pay_dividend(firm: Firm, shareholder: Household, amount: int, settlement_system: SettlementSystem):
        # The check and transfer are delegated to the SSoT
        success = settlement_system.transfer(
            buyer=firm, # Or whatever represents the source
            seller=shareholder, # Or whatever represents the destination
            amount=amount,
            memo=f"dividend_payment_{firm.id}"
        )
        if not success:
            logger.error("Failed to pay dividend due to insufficient funds.")
    ```

3.  **Deprecate and Remove**: Once all usages are migrated, delete the `IFinancialEntity` definition from `modules/finance/api.py`.

---

## 7. Mandatory Reporting Verification

All insights gathered during the analysis and design of this specification have been logged to `communications/insights/PH14-INTEGRITY-SWEEP.md`. This includes analysis of call sites for `IFinancialEntity` and performance considerations for the purity decorator. This mission is compliant with mandatory reporting protocols.
