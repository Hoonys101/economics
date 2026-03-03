1. **Understand Goals**: Fix "sales tax atomicity" and "inheritance leaks" based on AUDIT_SPEC_ECONOMIC.md.
2. **Analysis of Sales Tax Atomicity**:
    - The issue with Sales Tax Atomicity is likely the rollback function in `GoodsTransactionHandler` (`simulation/systems/handlers/goods_handler.py`).
    - The `rollback` method does:
      ```python
      success = context.settlement_system.transfer(destination, source, int(trade_value), f"rollback_goods:{tx.item_id}:{tx.id}")
      if context.taxation_system:
          intents = context.taxation_system.calculate_tax_intents(...)
          for intent in intents:
              context.settlement_system.transfer(context.government, source, int(intent.amount), f"rollback_tax:{intent.reason}:{tx.id}")
      ```
    - This is NOT ATOMIC. It uses multiple independent `transfer` calls. If one fails, we have a partial rollback.
    - **Fix for GoodsHandler rollback**: We should gather all `transfers` into a list and call `context.settlement_system.execute_multiparty_settlement(transfers, context.time)`.
    ```python
    transfers = []
    transfers.append((destination, source, int(trade_value)))
    if context.taxation_system:
        intents = context.taxation_system.calculate_tax_intents(...)
        for intent in intents:
            transfers.append((context.government, source, int(intent.amount)))
    success = context.settlement_system.execute_multiparty_settlement(transfers, context.time)
    ```

3. **Analysis of Inheritance Leaks**:
    - `InheritanceManager.process_death` has a lot of float operations and local variable `cash` state tracking that diverges from the single source of truth (`SettlementSystem.get_balance`).
    - It maintains `cash` as a float, does `cash += sale_price`, `cash -= tax_to_pay`, etc. It then creates transactions that execute asynchronously/synchronously.
    - If a transaction succeeds, it updates `cash`. But because it doesn't query SSoT for `cash`, `cash` can easily drift, especially with rounding (`round(cash, 2)`).
    - And `tx.total_pennies` is calculated using `int(cash * 100)` or `int(tax_to_pay * 100)`. Because of float imprecision, `int(0.1 * 100)` can sometimes be `9` instead of `10`. This leaks pennies.
    - It should strictly use SSoT (`simulation.settlement_system.get_balance(deceased.id, DEFAULT_CURRENCY)`), do ALL math in pennies (int), and use `transfer` or construct `Transaction` objects using `total_pennies`.
    - Wait, in `InheritanceManager.process_death`, it's manually building transactions. Let's fix it by migrating from `float` variables to strict `int` pennies variables (`cash_pennies`, `tax_amount_pennies`, `needed_pennies`, etc).
    - We must fetch `cash_pennies = deceased.get_balance()` using SSoT if possible, but the local logic seems to rely on `joint_share_ratio` for shared wallets. So we do:
      ```python
      wallet_balance = deceased._econ_state.wallet.get_balance(DEFAULT_CURRENCY)
      cash_pennies = int(wallet_balance * joint_share_ratio) # Wait, joint_share is float
      ```
      Actually, `wallet_balance` is ALREADY in pennies. So `cash_pennies = int(wallet_balance * joint_share_ratio)`.
    - Real estate value: `int(unit.estimated_value * 100)`.
    - Stock value: `int(price * 100)`.
    - Total wealth: sum of pennies.
    - Tax: `taxable_base_pennies = max(0, total_wealth_pennies - int(deduction * 100))`. `tax_amount_pennies = int(taxable_base_pennies * tax_rate)`.
    - When liquidating, `proceeds_pennies = int(share.quantity * price * 100)`.
    - Then update `cash_pennies += proceeds_pennies`.
    - This eliminates floats entirely from the calculation loops.

4. **Plan formulation**:
    1. Fix `simulation/systems/handlers/goods_handler.py`: Make `rollback` atomic by grouping all tax reversals and the main trade reversal into a single list of transfers and using `execute_multiparty_settlement`.
    2. Fix `simulation/systems/inheritance_manager.py`: Refactor `process_death` to exclusively use integer math for pennies (`cash_pennies`, `tax_amount_pennies`, etc) instead of floats.

5. **Let's examine `EscheatmentHandler.handle`**:
    - "EscheatmentHandler transfers ALL assets... Since we already paid tax, remaining cash is escheated."
    - In `EscheatmentHandler.handle` (Phase C):
      ```python
      balance = context.settlement_system.get_balance(buyer.id, DEFAULT_CURRENCY)
      if balance <= 0: return True
      credits = [(gov, balance, "escheatment")]
      success = context.settlement_system.settle_atomic(buyer, credits, context.time)
      ```
    - Wait, the `InheritanceManager` passes `price=cash, total_pennies=int(cash * 100)` but the `EscheatmentHandler` ignores `tx.total_pennies` and just transfers the ENTIRE `get_balance`. This is good, it means the `EscheatmentHandler` won't leak. However, `InheritanceManager` shouldn't have passed an inaccurate `total_pennies` in the first place.

6. Let's propose this plan via `request_plan_review`.
