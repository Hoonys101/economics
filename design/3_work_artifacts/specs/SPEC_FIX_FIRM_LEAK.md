# Technical Specification: Firm Management Money Leak Fix

**Target File**: `simulation/systems/firm_management.py`

## 1. Objective
Refactor `firm_management.py` to eliminate direct asset modification fallback for firm creation.

## 2. Required Changes

### 2.1. `spawn_firm`: Capital Injection
- **Current**: Has an `else` block fallback that uses `_sub_assets`/`_add_assets` if settlement system is missing (or just because).
- **New**:
  ```python
  settlement_system = simulation.settlement_system
  if not settlement_system:
      raise RuntimeError("SettlementSystem required for firm creation.")

  success = settlement_system.transfer(
      founder_household, 
      new_firm, 
      final_startup_cost, 
      f"Startup Capital for Firm {new_firm.id}",
      tick=simulation.time
  )

  if not success:
      # Log warning and return None (abort creation)
      return None
  ```

## 3. Constraints
- Remove any test-only hack or legacy fallback that allows creation without a valid transaction.
