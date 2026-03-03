1. **Understand Goals**: The user requested a "full economic integrity audit based on design/3_work_artifacts/specs/AUDIT_SPEC_ECONOMIC.md. Focus on sales tax atomicity and inheritance leaks."
2. **Reviewing AUDIT_SPEC_ECONOMIC.md**: The spec calls out Zero-Sum Violations (money supply creation/destruction), Transactional Atomicity (buyer debit and seller credit simultaneously), and Reflux Completeness (taxes/fees go to government/bank without leak).
3. **Analyze `InheritanceManager`**:
    - The `InheritanceManager.process_death` method has multiple direct mutations to a local `cash` variable instead of using `settlement_system.transfer`. It extracts the `wallet_balance`, does math on it, and then executes transactions, but doesn't actually pull/push the actual asset value properly in an atomic manner. It also uses `.execute` on the transaction processor which relies on other handlers to move the money, but it modifies `cash -= repay_amount` locally which is risky and creates state drift.
    - Also, lines like `cash = float(wallet_balance) * joint_share_ratio` use floats which violate the "no float casting for monetary calculations" rule (FloatIncursionError risk).
    - It creates transactions for `asset_liquidation`, `tax`, `escheatment`, and `inheritance_distribution`.
    - It iterates over transactions, executing them individually via `simulation.transaction_processor.execute(simulation, [tx])`. If one fails but another succeeds, it breaks atomicity. It should ideally package these together or rely on the transaction handlers (`InheritanceHandler`, `EscheatmentHandler`) which are already atomic.
    - The actual `InheritanceHandler.handle` receives the deceased agent as `buyer` and uses `settle_atomic`. It reads `total_pennies`, but where does the estate cash come from? The handler takes `total_pennies`, and distributes it. BUT the `InheritanceManager` sends multiple distinct transactions (tax, escheatment, distribution) which sequentially drain the balance.
4. **Analyze Sales Tax Atomicity**:
    - `GoodsTransactionHandler` calculates `intents = context.taxation_system.calculate_tax_intents(...)`.
    - It adds credits: `seller` gets `trade_value`, `government` gets `tax_amount`. Total cost is `trade_value + tax_amount`.
    - It calls `settlement_system.settle_atomic(buyer, credits, context.time)`. This is correctly atomic!
    - **Wait, if it's atomic, what is the issue?** Let's re-read the `TaxationSystem.calculate_tax_intents`.
    - Ah, in `TaxationSystem`, for goods: `sales_tax_rate` is used to calculate `tax_amount`. The intent sets `payer_id=buyer.id`.
    - `GoodsTransactionHandler` processes the intents: `if intent.payer_id == buyer.id: total_cost += amount_int`.
    - This seems fine. But let's check `CorporateTax` logic which is mentioned in the prompt ("Focus on sales tax atomicity and inheritance leaks." Wait, it specifically said "sales tax atomicity").
    - Let's check `GoodsTransactionHandler.rollback`.
    - `GoodsTransactionHandler.rollback` reverses the trade: `context.settlement_system.transfer(destination, source, int(trade_value), ...)`
    - Then it recalculates tax: `intents = context.taxation_system.calculate_tax_intents(...)`.
    - Then it reverses tax: `context.settlement_system.transfer(context.government, source, int(intent.amount), ...)`
    - **Issue with Sales Tax Atomicity in Rollback**: The rollback is NOT atomic! It executes multiple distinct `transfer` calls. If the government doesn't have enough funds (unlikely but possible), or if the first transfer succeeds but the second fails, we have a partial rollback (Zero-Sum Violation / Atomicity failure). It should aggregate them and use `execute_multiparty_settlement`.
5. **Fixing Inheritance Leaks**:
    - `InheritanceManager.process_death`: Needs to stop using `float()` and local `cash` mutation. It should use `int` (pennies).
    - Wait, the actual error is that `InheritanceManager` iterates over assets, calculates tax *using float math*, and issues sequential independent transactions.
    - And `InheritanceHandler.rollback` does use `execute_multiparty_settlement`, which is good. But the `InheritanceManager.process_death` is completely non-atomic. Wait, `process_death` is an event, not a transaction handler. It dispatches transactions. If a transaction fails, it just skips it.
    - But wait, look at `InheritanceManager.process_death` memory leaks reported:
        ```python
        cash = float(wallet_balance) * joint_share_ratio
        ...
        tax_amount = round(taxable_base * tax_rate, 2)
        ```
    - This is dealing with floats. `wallet_balance` is usually pennies now. If it's pennies, `float(wallet_balance) * joint_share_ratio` gives float pennies.
    - Instead, it should use integer math.
    - Also, `joint_share_ratio` is hardcoded?
    - Let's check `InheritanceManager.py` carefully.
