# Implementation Spec: Logic & Serialization Restoration
**Mission ID**: `PH15-LOGIC-CORE`
**Author**: Antigravity (derived from Gemini Scribe)
**Recipient**: Jules (Lead Developer)
**Date**: 2026-02-12

---

## 1. Overview
This specification focuses on restoring critical logic and data persistence capabilities. Specifically, it addresses the serialization gap in multi-slot inventories and the missing Quantitative Easing (QE) logic in the finance system.

---

## 2. Module 1: `AgentStateDTO` Multi-Inventory Serialization
**Addresses**: `TD-AGENT-STATE-INVFIRM`

### 2.1. API & DTO Specification (`modules/common/dtos.py` or equivalent)

The `AgentStateDTO` will be updated to support a dictionary of inventories, where each key is a named slot (e.g., "MAIN", "INPUT").

```python
from typing import Dict, List
from pydantic import BaseModel, Field

class ItemDTO(BaseModel):
    name: str
    quantity: float
    quality: float = 100.0

class InventorySlotDTO(BaseModel):
    items: List[ItemDTO] = Field(default_factory=list)

# In modules/common/dtos.py (or agent-specific DTO file)
class AgentStateDTO(BaseModel):
    # ... existing fields like agent_id, class_name, balance_pennies ...

    # NEW: Replace single inventory with a dictionary of inventory slots
    inventories: Dict[str, InventorySlotDTO] = Field(default_factory=dict)
```

### 2.2. Implementation: Firm `load_state` & `get_state` (Pseudo-code)

The `Firm` orchestrator will be responsible for packing and unpacking the new `inventories` structure.

```python
# In modules/firm/orchestrator.py (or equivalent Firm class)

class Firm:
    def get_state(self) -> AgentStateDTO:
        """Packs the firm's current state into a DTO, including all inventory slots."""
        inventory_dtos: Dict[str, InventorySlotDTO] = {}
        for slot_name in self.inventory_manager.get_slot_names():
            slot = self.inventory_manager.get_slot(slot_name)
            inventory_dtos[slot_name] = slot.to_dto() 

        return AgentStateDTO(
            # ... other fields ...
            inventories=inventory_dtos
        )

    def load_state(self, state: AgentStateDTO):
        """Loads state from a DTO, populating all inventory slots."""
        # Unpack the new `inventories` structure
        for slot_name, slot_dto in state.inventories.items():
            target_slot = self.inventory_manager.get_or_create_slot(slot_name)
            target_slot.from_dto(slot_dto)
```

### 2.3. Testing & Verification Strategy
1. **Create Test**: `tests/system/test_serialization.py::test_firm_multi_inventory_save_load`.
2. **Logic**: Save a firm with multiple slots, load into a new object, and assert equality.

---

## 3. Module 2: Quantitative Easing (QE) Logic in `FinanceSystem`
**Addresses**: `TD-QE-MISSING`, `TDL-031`

### 3.1. Implementation: `issue_treasury_bonds` (Pseudo-code)

The logic will be inserted into `FinanceSystem.issue_treasury_bonds` to dynamically select the bond buyer.

```python
# In modules/finance/system.py

class FinanceSystem(IFinanceSystem):
    def issue_treasury_bonds(self, amount: int, current_tick: int) -> Tuple[List[BondDTO], List[Transaction]]:
        # 1. Get QE Trigger Data
        debt_to_gdp_ratio = self.fiscal_monitor.get_debt_to_gdp() 
        qe_threshold = self.config_module.get("economy_params.QE_DEBT_TO_GDP_THRESHOLD", 1.5)

        # 2. Select Buyer Agent Handle
        if debt_to_gdp_ratio > qe_threshold:
            buyer_agent = self.central_bank # QE ACTIVE
        else:
            buyer_agent = self.bank         # NORMAL

        # 3. Execute Transfer via SettlementSystem
        success = self.settlement_system.transfer(
            buyer_agent,   
            self.government,
            amount,
            memo=f"bond_purchase_{tick}",
            currency=DEFAULT_CURRENCY
        )
```

### 3.2. Testing & Verification Strategy
1. **Modify Test**: Update `tests/unit/modules/finance/test_double_entry.py` (or applicable file) to verify buyer switching based on debt thresholds.
2. **Scenario**: Mock debt-to-gdp above/below threshold and verify the `buyer_agent` passed to `transfer`.
