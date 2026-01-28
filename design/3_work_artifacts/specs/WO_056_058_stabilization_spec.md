To: **Antigravity (Team Leader)**
From: **Gemini (Administrative Assistant)**
Subject: **Draft Spec: System Stabilization (WO-056 & WO-058.1)**

I have prepared the **Zero-Question Technical Specification** for the System Stabilization Work Orders. This spec addresses the confirmed Money Leak in Government real estate transactions and the Inventory Glut "Death Spiral" in firms.

### **Document Registry Update**
- **Target Spec:** `design/specs/WO_056_058_stabilization_spec.md`
- **Target Interface:** `modules/economy/stabilization/api.py`
- **Status:** Draft Ready for Review.

---

### **1. `modules/economy/stabilization/api.py`**

```python
"""
modules/economy/stabilization/api.py

Defines the contracts and data structures required for:
1. WO-056: Correctly tracking money removed from M1 via Government Asset Sales.
2. WO-058.1: Preventing Firm Inventory Glut via production caps.
"""
from typing import Protocol, TypedDict, runtime_checkable, Optional, Dict

# --- DTOs ---

class AssetSaleRecord(TypedDict):
    """Data object for recording a government asset sale for audit trails."""
    tick: int
    buyer_id: int
    item_id: str
    price: float
    quantity: float
    total_value: float
    asset_type: str  # e.g., "real_estate", "bond"

class ProductionConstraintDTO(TypedDict):
    """Configuration for Firm Production Logic."""
    inventory_cap_multiplier: float  # e.g., 2.0 (Stop producing if Inv > 2x Target)
    min_sales_velocity: float        # Minimum sales required to justify full production

# --- Interfaces ---

@runtime_checkable
class MonetaryAuthority(Protocol):
    """
    Interface for an entity that can destroy/withdraw money from circulation (M1).
    Implemented by: Government
    """
    def record_asset_sale(self, amount: float, details: AssetSaleRecord) -> None:
        """
        Records the sale of a public asset.
        
        Effect:
            - Increases the entity's internal 'money_destroyed' or 'treasury' counter.
            - Used by the EconomicTracker to balance the Money Supply equation:
              (M1 + Money_Destroyed = Issued_Base)
        """
        ...

@runtime_checkable
class InventoryManagedEntity(Protocol):
    """
    Interface for an entity (Firm) that must manage inventory levels.
    """
    input_inventory: Dict[str, float]
    inventory: Dict[str, float]
    production_target: float
    
    def check_inventory_glut(self, constraint: ProductionConstraintDTO) -> bool:
        """
        Determines if production should be halted due to overstock.
        Returns: True if production should be skipped/throttled.
        """
        ...
```

---

### **2. `design/specs/WO_056_058_stabilization_spec.md`**

```markdown
# Spec: System Stabilization (Money Leak & Inventory Glut)

**Phase:** Maintenance (22.5)
**Work Orders:** WO-056 (Money Leak), WO-058.1 (Inventory Glut)
**Author:** Gemini (Admin Assistant)
**Reviewer:** Antigravity

## 1. Overview
This specification patches two critical systemic failures identified in recent audits:
1.  **Money Leak (-999.8/tick)**: Caused by `HousingSystem` transferring money from M1 Agents (Households) to the Government (Non-M1) without recording the withdrawal in the `monetary_delta` ledger.
2.  **Inventory Glut Death Spiral**: Firms continue producing goods despite zero sales, leading to massive storage costs and inevitable bankruptcy.

---

## 2. Component Design & Logic

### 2.1. Money Leak Fix: Government Asset Sales
**Module:** `simulation/systems/housing_system.py` / `simulation/agents/government.py`

#### **Context**
Currently, when Government sells a house, `seller.assets += value`. If Government is outside M1, this money "disappears" from the M1 tracker view unless explicitly logged as `money_destroyed` or `tax_collected`.

#### **Interface Changes**
- `Government` class must implement `MonetaryAuthority` protocol (defined in `api.py`).

#### **Pseudo-code Logic: `HousingSystem.process_transaction`**

```python
def process_transaction(self, tx: Transaction, simulation: Simulation):
    # ... existing validation ...
    trade_value = tx.price * tx.quantity
    
    # 1. Deduct from Buyer (M1)
    buyer.assets -= trade_value
    
    # 2. Transfer to Seller
    seller = simulation.agents.get(tx.seller_id)
    
    # [NEW LOGIC START]
    if isinstance(seller, MonetaryAuthority): # e.g., Government
        # Create Audit Record
        record = AssetSaleRecord(
            tick=simulation.time,
            buyer_id=buyer.id,
            item_id=tx.item_id,
            price=tx.price,
            quantity=tx.quantity,
            total_value=trade_value,
            asset_type="real_estate"
        )
        
        # Invoke Interface: This updates 'monetary_delta' or 'total_money_destroyed'
        seller.record_asset_sale(trade_value, record)
        
        # Note: Do NOT add to seller.assets if the intent is to simulate "destruction" 
        # or removal from M1. If Govt keeps assets, EconomicTracker must know Govt Assets are OUTSIDE M1.
        # Current Design Assumption: Govt Assets are tracked separately. 
        # Just incrementing assets is fine IF tracker accounts for it.
        # AUDIT FINDING: Tracker expects 'monetary_delta' to increase when money leaves M1.
        
    else:
        # Standard Transfer
        seller.assets += trade_value
    # [NEW LOGIC END]
```

### 2.2. Reflux Remainder Leak
**Module:** `simulation/systems/reflux_system.py`

#### **Problem**
`distribute()` method calculates `per_capita = total / count` and then sets `self.balance = 0.0`. The remainder `total - (per_capita * count)` is deleted from existence.

#### **Pseudo-code Logic: `RefluxSystem.distribute`**

```python
def distribute(self, recipients: List[Agent]):
    if not recipients or self.balance <= 0:
        return

    count = len(recipients)
    amount_per_agent = self.balance / count  # Float division
    
    # OPTION A: Distribute exact float (No leak, but float precision issues over time)
    # OPTION B: Truncate to 2 decimals and keep remainder (Safer for discrete currency)
    
    # Selected Approach: Float preservation (Simpler)
    for agent in recipients:
        agent.assets += amount_per_agent
        
    # LOGIC FIX:
    # Instead of self.balance = 0.0, subtract what was ACTUALLY given.
    # But with float division, sum(amount_per_agent) == self.balance (approx).
    # To be safe against float drift:
    
    actual_distributed = amount_per_agent * count
    self.balance -= actual_distributed 
    
    # Clamp to 0 if close to epsilon to prevent -0.0000001
    if abs(self.balance) < 1e-9:
        self.balance = 0.0
```

### 2.3. Inventory Glut Prevention (The "Brake Pedal")
**Module:** `simulation/firms.py`

#### **Context**
Firms produce blindly. Need a feedback loop to stop production when inventory is high relative to sales.

#### **Pseudo-code Logic: `Firm.produce`**

```python
def produce(self, current_time: int):
    # [NEW LOGIC START]
    # Configuration Constants
    INVENTORY_CAP_MULTIPLIER = 3.0  # Allow up to 3x production target in stock
    
    item_id = self.specialization
    current_stock = self.inventory.get(item_id, 0.0)
    
    # Check 1: Absolute Cap based on Production Target
    max_allowed = self.production_target * INVENTORY_CAP_MULTIPLIER
    
    if current_stock >= max_allowed:
        self.logger.info(f"GLUT_PROTECTION | Skipping production. Stock {current_stock} >= Max {max_allowed}")
        self.current_production = 0.0
        return
        
    # Check 2 (Optional Smart Logic): Sales Velocity
    # If using 'last_sales_volume' from FinanceDepartment
    if self.finance.last_sales_volume == 0 and current_stock > self.production_target:
        # If we sold NOTHING last tick and have enough for this tick, don't produce more.
        self.logger.info("GLUT_PROTECTION | Zero sales detected. Halting production.")
        self.current_production = 0.0
        return
    # [NEW LOGIC END]

    # ... Proceed with existing Cobb-Douglas Logic ...
```

---

## 3. Verification Plan

### 3.1. Golden Sample Tests
1.  **Money Leak Test**:
    - Scenario: Gov sells property for 1000.
    - Check: `Gov.money_destroyed` (or equivalent delta tracker) increases by 1000.
    - Check: `EconomicTracker` reports `Leak == 0`.
2.  **Inventory Glut Test**:
    - Scenario: Force `Firm.sales = 0` for 10 ticks.
    - Check: `Firm.inventory` plateaus at `Target * 3`.
    - Check: `Firm.assets` do not drain purely from holding costs of infinite inventory.

---

## 4. Mandatory Reporting

**[Insight & Tech Debt Reporting Instruction]**
> Jules, upon completing this implementation, you MUST:
> 1.  Run the simulation for at least 50 ticks to verify the "Money Leak" metric in logs is stable (near 0).
> 2.  Observe Firm bankruptcy rates. If the "Glut Protection" is too aggressive and causes shortages, note this in `communications/insights/WO_058_tuning.md`.
> 3.  Append any new "Magic Numbers" (e.g., `INVENTORY_CAP_MULTIPLIER`) created during tuning to `TECH_DEBT_LEDGER.md` for future extraction to `config.py`.
```
