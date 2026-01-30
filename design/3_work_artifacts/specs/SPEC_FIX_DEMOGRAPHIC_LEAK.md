# Technical Specification: Demographic & Inheritance Zero-Sum Fix

**Target File**: `simulation/systems/demographic_manager.py`

## 1. Objective
Refactor `demographic_manager.py`, specifically `handle_inheritance`, to ensure mathematical zero-sum integrity and eliminate direct asset modification.

## 2. Required Changes

### 2.1. `handle_inheritance`: Estate Distribution
- **Issues Highligted by Audit**:
  - `_sub_assets` is used to clear deceased assets (opaque).
  - Floating point division `share = net / len` leaves residuals (evaporation).
  - Direct calls bypass ledger.

- **New Logic**:
  1.  **Strict Amount Calculation**:
      ```python
      total_assets = deceased_agent.assets
      if total_assets <= 0: return
      
      tax_amount = total_assets * TAX_RATE
      net_estate = total_assets - tax_amount
      ```
  
  2.  **Tax Transfer**:
      ```python
      simulation.settlement_system.transfer(deceased_agent, government, tax_amount, "inheritance_tax", tick=simulation.time)
      ```

  3.  **Heir Distribution with Residual Handling**:
      ```python
      if heirs:
          share = math.floor((net_estate / len(heirs)) * 100) / 100.0  # Floor to 2 decimals
          distributed = 0.0
          
          # Distribute shares
          for i, heir in enumerate(heirs):
              # Last heir gets the remainder to ensure sum(shares) == net_estate
              if i == len(heirs) - 1:
                   amount_to_send = net_estate - distributed
              else:
                   amount_to_send = share
              
              simulation.settlement_system.transfer(deceased_agent, heir, amount_to_send, "inheritance_distribution", tick=simulation.time)
              distributed += amount_to_send
      else:
          # No heirs: Escheatment to State
          simulation.settlement_system.transfer(deceased_agent, government, net_estate, "escheatment", tick=simulation.time)
      ```

  4.  **No explicit `_sub_assets`**: The transfers will naturally drain the `deceased_agent`'s balance to near zero (or exactly zero).

## 3. Constraints
- **Imports**: Ensure `math` is imported.
- **Safety**: Check `if not simulation.settlement_system: raise RuntimeError`.
