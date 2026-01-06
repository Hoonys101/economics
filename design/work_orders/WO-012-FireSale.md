# Work Order: Operation "Fire Sale" (Breaking Price Rigidity)

> **To**: Jules (Implementation Agent)
> **From**: Architect Prime (via Antigravity)
> **Priority**: Critical (Hotfix for Economic Survival)
> **Codename**: Survival Instinct

## 1. Diagnosis

The economy suffers from **Dual Rigidity**:
- **Wage Rigidity**: Households refuse to work below 10.0 (Fixed: lowered to 6.0)
- **Price Rigidity**: Firms refuse to lower prices even with excess inventory (NEW)

AI learns slowly. Before it learns "cash flow matters more than margin", the Firm goes bankrupt.

## 2. Implementation: Panic Pricing Mechanism

### Target File: `simulation/decisions/ai_driven_firm_engine.py`

Add a method `apply_inventory_pressure()` and call it in the pricing decision flow:

```python
def apply_inventory_pressure(self, firm, proposed_price):
    """
    Heuristic Override: Forces price reduction when inventory is excessive.
    'AI is dumb, so Instinct takes over.'
    """
    # Target inventory = 3 days of production capacity
    target_inventory = getattr(firm, 'production_capacity', 10) * 3
    current_inventory = sum(firm.inventory.values()) if isinstance(firm.inventory, dict) else firm.inventory
    
    if current_inventory > target_inventory:
        excess_ratio = current_inventory / max(target_inventory, 1)
        
        # 2x inventory -> 5% discount, 5x -> 20%, max 50%
        discount_rate = min(0.50, (excess_ratio - 1.0) * 0.05)
        
        # Force price down
        panic_price = proposed_price * (1.0 - discount_rate)
        
        # Floor price (never below 0.1)
        return max(0.1, panic_price)
        
    return proposed_price
```

### Integration Point

In the method where `sell_price` is determined, wrap the final price:

```python
final_price = self.apply_inventory_pressure(agent, proposed_price)
```

## 3. Verification

1. Run Iron Test: `python scripts/iron_test.py`
2. Success Criteria:
   - Active Households > 10 at Tick 1000
   - Logs show decreasing prices when inventory is high

## 4. Insight Report

After implementation, report:
- Did trades start happening?
- At what tick did prices stabilize?
- Final survival rate
