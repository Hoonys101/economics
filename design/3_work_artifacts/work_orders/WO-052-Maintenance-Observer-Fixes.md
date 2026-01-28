# Work Order: WO-052-Maintenance-Observer-Fixes

**Date:** 2026-01-12
**Phase:** Maintenance
**Assignee:** Jules (Worker AI)
**Objective:** Resolve critical issues identified in `daily_action_plan_20260111.md`: Asset Leak in Inheritance and Scanner False Positives.

## 1. Task 1: Fix Asset Leak in Inheritance (No Heir Case)

**Target File:** `simulation/systems/inheritance_manager.py`
**Method:** `process_death`
**Logic:**
Currently, if `not heirs` is True, only `deceased.assets` (Cash) is confiscated. Stocks and Real Estate are ignored, creating "Zombie Assets".

**Implementation:**
In the `if not heirs:` block (around line 178), add logic to confiscate Stocks and Real Estate before returning.

```python
        if not heirs:
            # 1. State Confiscation (Cash)
            surplus = deceased.assets
            if surplus > 0:
                deceased.assets = 0
                simulation.government.assets += surplus
                self.logger.info(
                    f"NO_HEIRS | Confiscated cash {surplus:.2f} to Government.",
                    extra={"agent_id": deceased.id}
                )

            # 2. State Confiscation (Stocks) -- NEW
            # Transfer all remaining shares to Government
            for firm_id, share in list(deceased.portfolio.holdings.items()):
                 qty = share.quantity
                 if qty > 0:
                     # Update Shareholder Registry: Deceased -> 0, Govt -> +qty
                     if simulation.stock_market:
                         simulation.stock_market.update_shareholder(deceased.id, firm_id, 0)
                         # Assuming Government doesn't actively trade or track portfolio object, 
                         # but we should register it in the market at least.
                         simulation.stock_market.update_shareholder(simulation.government.id, firm_id, qty) # Add logic if needed
            
            # Clear Deceased Portfolio
            deceased.portfolio.holdings.clear()
            deceased.shares_owned.clear()

            # 3. State Confiscation (Real Estate) -- NEW
            # Transfer all remaining properties to Government
            remaining_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
            for unit in remaining_units:
                unit.owner_id = simulation.government.id
                # Remove from Deceased list (if maintained elsewhere, but here we iterate simulation list)
                # Ensure deceased.owned_properties is cleared below.
            
            deceased.owned_properties.clear()
            
            self.logger.info(
                 f"NO_HEIRS_ASSETS | Confiscated {len(remaining_units)} properties and portfolio to Government.",
                 extra={"agent_id": deceased.id}
            )

            return
```

## 2. Task 2: Fix Observer Scanner False Positives

**Target File:** `scripts/observer/scan_codebase.py`
**Logic:**
Exclude the `scripts/observer` directory from the scan loop to prevent the scanner from flagging its own keyword definitions (e.g., searches for "TODO", "FIXME").

**Implementation:**
Locate the `os.walk` loop (likely in `scan_directory` or `main`).
Add filtering condition:

```python
    # Inside os.walk loop
    for root, dirs, files in os.walk(params['root_dir']):
        # Exclude .git, __pycache__, etc. (Existing)
        
        # NEW: Exclude observer script directory to avoid self-flagging
        if "scripts\\observer" in root or "scripts/observer" in root:
            continue
```
*Note: Ensure cross-platform path compatibility or check if `scan_codebase.py` is in the path.*

