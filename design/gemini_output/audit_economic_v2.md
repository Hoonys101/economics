# Economic Integrity & Leak Audit V2
**Mission:** [AUDIT-ECONOMIC-V2]
**Target:** Identify "Zero-Sum Violations" (Asset Creation/Evaporation)

## [발견된 누출 지점 리스트]

### 1. Inheritance Distribution Rounding Error
*   **File:** `simulation/systems/transaction_processor.py`
*   **Location:** `execute_transaction` method, `elif tx.transaction_type == "inheritance_distribution":` block.
*   **Severity:** Low (Floating Point Drift) but cumulative.
*   **Description:**
    The code calculates `amount_per_heir = total_cash / len(heir_ids)`.
    If `total_cash` is not perfectly divisible by `len(heir_ids)`, the remainder (e.g., `0.333...`) is left in the `buyer` (Deceased Agent) account.
    Since the Deceased Agent is subsequently removed from the simulation without a final sweep of this residual cash, the money effectively evaporates.

### 2. Household Liquidation Asset Evaporation
*   **File:** `simulation/systems/lifecycle_manager.py`
*   **Location:** `_handle_agent_liquidation` method, `Household Liquidation` section.
*   **Severity:** Critical (Potential large leaks if inheritance fails).
*   **Description:**
    The code explicitly clears `household.inventory` and `household.shares_owned`. However, unlike the `Firm Liquidation` block (which has a check `if firm.assets > 1e-6: firm._sub_assets(...)`), there is **no check** to ensure `household.assets` is 0.0 before the agent is removed from the `state.agents` list.
    Any residual cash (from the inheritance rounding error above, or if inheritance transactions fail) is permanently destroyed without being recorded in `Government.total_money_destroyed`.

## [원자성 위반 코드 블록]

### 1. Asset Liquidation (Money Creation)
*   **File:** `simulation/systems/transaction_processor.py`
*   **Code:**
    ```python
    elif tx.transaction_type == "asset_liquidation":
        # Special Minting Logic + Asset Transfer
        # Buyer (Gov) -> Seller (Agent). No Debit.
        seller.deposit(trade_value)
        if hasattr(buyer, "total_money_issued"):
            buyer.total_money_issued += trade_value
    ```
*   **Analysis:**
    This logic intentionally violates the `Buyer.assets -= TradeValue` rule. It credits the Seller without debiting the Buyer (Government).
    **Proof:** `Buyer Delta (0) != Seller Delta (+TradeValue) + Tax (0)`.
    **Context:** This is a "Minting" operation (Quantitative Easing). While it technically creates money, it tracks it via `total_money_issued`. It is an "Authorized Violation" of Zero-Sum, but must be strictly monitored.

### 2. Goods Transaction (Atomicity Confirmed)
*   **File:** `simulation/systems/transaction_processor.py`
*   **Code:**
    ```python
    if settlement:
        success = settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")
        if success and tax_amount > 0:
            # Atomic collection from buyer
            government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer, current_time)
    ```
*   **Analysis:**
    The deduction from Buyer is `TradeValue` (via settlement) + `TaxAmount` (via collect_tax).
    The addition to Seller is `TradeValue`.
    The addition to Government is `TaxAmount`.
    **Proof:** `Buyer Delta (-(P+T)) == Seller Delta (+P) + Gov Delta (+T)`.
    **Result:** Mathematically consistent, provided `collect_tax` succeeds. If `collect_tax` fails (e.g. insufficient funds after the first transfer), the tax is uncollected, but money is not destroyed/created, just retained by the buyer.

## [해결을 위한 슈도코드]

### Solution 1: Exact Inheritance Distribution
**Target:** `simulation/systems/transaction_processor.py`

```python
# [Pseudocode Fix]
elif tx.transaction_type == "inheritance_distribution":
    heir_ids = tx.metadata.get("heir_ids", [])
    total_cash = buyer.assets

    if total_cash > 0 and heir_ids:
        count = len(heir_ids)
        # 1. Floor division to guarantee safe amount
        base_amount = math.floor((total_cash / count) * 100) / 100.0

        # 2. Distribute base amount to all except last
        for i in range(count - 1):
             heir = agents.get(heir_ids[i])
             settlement.transfer(buyer, heir, base_amount, "inheritance_part")

        # 3. Give EVERYTHING remaining to the last heir (Exact Distribution)
        # This captures the 0.000...1 residuals
        last_heir = agents.get(heir_ids[-1])
        remaining = buyer.assets # Should be base_amount + dust
        settlement.transfer(buyer, last_heir, remaining, "inheritance_final")
```

### Solution 2: Household Liquidation Dust Sweeper
**Target:** `simulation/systems/lifecycle_manager.py`

```python
# [Pseudocode Fix]
# Inside _handle_agent_liquidation for Households
for household in inactive_households:
    # ... existing processing ...

    # [NEW] Final Dust Sweep
    if household.assets > 0:
        # Option A: Escheat to Government (Revenue)
        # state.government.collect_tax(household.assets, "death_dust_sweep", household, state.time)

        # Option B: Record as Destruction (if we want to just delete it safely)
        dust = household.assets
        household._sub_assets(dust)
        if hasattr(state.government, "total_money_destroyed"):
            state.government.total_money_destroyed += dust
```
