# Work Order: WO-049-Legacy-Protocol (Inheritance System)

**Date:** 2026-01-11
**Phase:** Phase 22 (The Awakening) - Step 2 (Infrastructure)
**Assignee:** Jules (Worker AI)
**Objective:** 에이전트 사망 시 자산(현금, 부동산, 주식)을 평가, 과세, 처분하여 상속인(Heir)에게 자본을 손실 없이 이전한다.

## 1. System Architecture
*   **New Module:** `simulation/systems/inheritance_manager.py`
*   **Class:** `InheritanceManager`
*   **Role:** Death Event Handler. Asset Valuation -> Taxation -> Transfer.

## 2. Process Flow Logic (The Pipeline)

### Step 1. Estate Valuation (유산 평가)
$$ TotalWealth = Cash + (House \times P_{market}) + (Stocks \times P_{current}) $$
*   Evaluate all assets at CURRENT market price.

### Step 2. Taxation (상속세 징수)
*   `Taxable_Base = max(0, TotalWealth - INHERITANCE_DEDUCTION)`
*   `Tax_Amount = Taxable_Base * INHERITANCE_TAX_RATE`
*   **Liquidity Check (Crucial):**
    *   `if Cash >= Tax_Amount`: Pay from Cash.
    *   `else`: **Forced Liquidation**.
        1.  Sell Stocks (Market Order).
        2.  Sell Real Estate (Fire Sale at 90% Price to Engine/Market).
        3.  If still insufficient -> Bankruptcy Inheritance (Heir gets 0, Tax Debt erased).

### Step 3. Transfer (자산 이전)
*   **Target (Heir)**: `agent.children` (Living only).
    *   If multiple children: Split `Net_Estate` equally (N분의 1).
    *   If no children: State confiscation (Government revenue).
*   **Hanodver**:
    *   `Cash`: Add to Heir's wallet.
    *   `RealEstate`: Update Registry Owner ID.
    *   `Stock`: Transfer share counts to Heir's Portfolio.

### Step 4. Cleanup (Reincarnation)
*   Unregister Agent ID from Simulation Registry.
*   Log Outcome: `logs/inheritance.log`.

## 3. Implementation Details

### Config (`config.py`)
```python
INHERITANCE_TAX_RATE = 0.4      # 40%
INHERITANCE_DEDUCTION = 10000   # Basic Deduction
```

### Module (`InheritanceManager`)
```python
class InheritanceManager:
    def process_death(self, deceased: Household, government: Government):
        # 1. Valuation
        # 2. Tax Collection (Liquidate if needed)
        # 3. Distribute Remainder to Heirs
        # 4. Cleanup
```

## 4. Verification Plan
*   **Test Case 1 (Standard)**: Rich parent dies -> Tax paid -> Child gets remaining wealth.
*   **Test Case 2 (Liquidity Crisis)**: Parent has House but no Cash -> Review verifies House is sold to pay tax -> Child inherits remainder cash.
*   **Test Case 3 (No Heir)**: Wealth transfers to Government.
