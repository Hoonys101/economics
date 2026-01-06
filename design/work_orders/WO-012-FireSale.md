# Work Order: Operation "Fire Sale" - REVISED (Solvency-Driven Pricing)

> **To**: Jules (Implementation Agent)
> **From**: Architect Prime (via Antigravity)
> **Priority**: Critical (Hotfix for Economic Survival)
> **Codename**: Survival Instinct
> **Revision**: v2 - Changed from Inventory-based to Solvency-based model

## ⚠️ Important: Previous Logic DEPRECATED

The inventory-based dumping logic was **incorrect**. It modeled modern JIT optimization, not survival instincts.

**New Model**: Price drops when **cash runs out**, not when **inventory piles up**.

## 1. Core Concept

| Trigger | Old (WRONG) | New (CORRECT) |
|---|---|---|
| What | "Inventory > Target" | "Cash is running out" |
| Why | Efficiency (JIT) | Survival (Solvency) |
| Real-world | Modern supply chain | 19th century merchant panic |

## 2. Implementation: `calculate_survival_price()`

### Target File: `simulation/decisions/ai_driven_firm_engine.py`

Replace any inventory-based logic with:

```python
def calculate_survival_price(self, firm, proposed_price):
    """
    Solvency-Driven Pricing.
    - Depreciation: Old inventory loses value.
    - Liquidity Fear: Low cash triggers panic selling.
    """
    # --- 1. Depreciation Pressure ---
    # Longer inventory holding = lower value (0.5% decay per day)
    sales_volume = getattr(firm, 'sales_volume', 1) or 1
    current_inventory = sum(firm.inventory.values()) if isinstance(firm.inventory, dict) else getattr(firm, 'inventory', 0)
    avg_inventory_days = current_inventory / sales_volume
    depreciation_factor = max(0.5, 1.0 - (avg_inventory_days * 0.005))
    
    value_adjusted_price = proposed_price * depreciation_factor
    
    # --- 2. Liquidity Fear (Runway-based Panic) ---
    fixed_cost = getattr(firm, 'fixed_cost', 0) or 0
    wages = getattr(firm, 'wages_paid_this_tick', 0) or 0
    daily_burn = fixed_cost + wages
    runway = firm.assets / (daily_burn + 1e-9)  # Days until bankruptcy
    
    panic_discount = 0.0
    if runway < 30:   # Less than 1 month
        panic_discount = 0.10  # 10% off
    if runway < 10:   # Less than 10 days
        panic_discount = 0.30  # 30% off
    if runway < 3:    # Imminent death
        panic_discount = 0.80  # 80% off (true fire sale)
        
    final_price = value_adjusted_price * (1.0 - panic_discount)
    
    # Floor price (never below 0.1)
    return max(0.1, final_price)
```

### Integration

Call this method when determining `sell_price`:

```python
final_price = self.calculate_survival_price(agent, proposed_price)
```

## 3. Economic Insight

> **"Rich firms hold prices. Poor firms dump."**

- Cash-rich firms: Can afford to wait. Keep prices high.
- Cash-poor firms: Must sell NOW. Slash prices.
- This creates natural **Market Stratification** and **M&A opportunities**.

## 4. Verification

1. Run Iron Test: `python scripts/iron_test.py`
2. Report:
   - Survival rate at Tick 1000
   - Did trades happen?
   - Any "Panic Discount" logs appearing?
