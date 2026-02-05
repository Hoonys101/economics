An `IntegrityError` is occurring at Tick 50 because a `Transaction` record is being created with a `NULL` `seller_id` during a firm's IPO process.

Here is the step-by-step analysis of the root cause:

1.  **Firm Creation**: In `simulation/systems/firm_management.py`, the `spawn_firm` function orchestrates the creation of a new firm.
2.  **Capital Transfer**: It calls `settlement_system.transfer()` to move startup capital from the founder to the new firm. This creates a valid `Transaction` for the currency transfer where `debit_agent` (the founder) and `credit_agent` (the new firm) both have valid IDs.
3.  **IPO Initialization**: Immediately after, `new_firm.init_ipo()` is called. This function's responsibility is to issue the initial shares to the founder.
4.  **Transaction Creation Flaw**: The flaw lies within the `init_ipo` method (located in `simulation/firms.py`, which was not provided but can be inferred). This method creates a `Transaction` record to represent the issuance of shares. It correctly sets the `buyer_id` to the founder, but it sets the `seller_id` to `None`. The logical seller for an IPO is the issuing firm itself, but this was omitted.
5.  **Database Crash**: This invalid `Transaction` object is added to the simulation's transaction buffer. At the end of the tick, the `PersistenceManager` attempts to save all buffered transactions to the database, leading to the `NOT NULL constraint failed: transactions.seller_id` error.

The log entry `IPO | Firm 127 initialized IPO with 1000.0 shares. Par value: 30.00` confirms this IPO event occurs just before the crash. The fix is to ensure that the firm's own ID is used as the `seller_id` in the IPO transaction.

I will now apply the fix.
