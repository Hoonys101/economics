I will now generate a detailed report diagnosing the seven test failures, focusing on the root causes and providing specific recommendations for fixes. The report will be saved to `reports/final_seven_diagnosis.md`.
I was unable to write the findings to `reports/final_seven_diagnosis.md` due to a tool execution error. I am providing the full report content below in markdown format as requested.

# Final Seven Failures: Deep-Dive Diagnosis

## Executive Summary
The analysis of the remaining seven test failures points to two primary categories of issues. First, critical integration tests are failing with `0.0` balances due to incomplete business logic in modules like `LiquidationManager` and `TransactionManager`, which fail to account for multi-currency transfers and special seller cases (e.g., public auctions). Second, a cluster of `TypeError` and protocol-related failures stems from the project's transition to stricter, protocol-based interfaces (`IFinancialAgent`, `IPropertyOwner`). Legacy agents and mock objects that do not fully comply with these new contracts cause errors in `SettlementSystem` and various handlers, while complex atomic transactions and inheritance procedures have fragile rollback and asset transfer logic, leading to state inconsistencies and memory leaks.

## Detailed Analysis

### Failure 1 & 2: Integration Tests Return `0.0` Balances

These failures indicate that money or assets are not reaching their destination during complex economic events.

- **Symptom 1: Multi-Currency Liquidation Fails**
  - **Status**: ❌ **Logic Error**
  - **Analysis**: During firm liquidation, foreign currency assets (e.g., "KRW") are not being distributed to shareholders, resulting in them receiving only the `DEFAULT_CURRENCY` portion or nothing. The `LiquidationManager` module, which orchestrates the payout, appears to be processing only the default currency from the firm's multi-currency balance.
  - **Evidence**: `tests/integration/test_multicurrency_liquidation.py:L70-89` clearly shows the design intent: both USD and KRW should be transferred to the shareholder. The `SettlementSystem.transfer` method correctly accepts a `currency` parameter (`simulation/systems/settlement_system.py:L513`), confirming the bug lies in the calling module.
  - **Fix Recommendation**: Modify `LiquidationManager` to iterate through all key-value pairs in the liquidated firm's multi-currency balance (`firm.finance.balance`). For each currency, a call to `SettlementSystem.transfer` must be made to distribute the correct amount to the respective shareholders.

- **Symptom 2: Public Manager Treasury Remains `0.0` After Asset Sales**
  - **Status**: ❌ **Logic Error**
  - **Analysis**: The `PublicManager`'s treasury is not credited after it sells liquidated assets on the market. The `TransactionManager` is responsible for settling these trades but fails to recognize the `PublicManager` (identified by `seller_id=-1`) as the recipient of the funds.
  - **Evidence**: `tests/integration/test_public_manager_integration.py:L84-93` shows `TransactionManager.execute()` being called, after which the test asserts that the `PublicManager`'s treasury has increased. The transaction object `tx` is explicitly created with `seller_id=-1`.
  - **Fix Recommendation**: Update `TransactionManager.execute()` with a specific conditional branch to handle transactions where `seller_id == -1`. Inside this branch, the logic must retrieve the `PublicManager` instance from the simulation state and explicitly credit its `system_treasury` with the proceeds from the sale.

### Failure 3, 4, & 5: `TypeError` and Protocol Mismatches

These errors are caused by a disconnect between new, strictly-defined interfaces and older or incomplete implementations.

- **Symptom 3: `TypeError` in `SettlementSystem`**
  - **Status**: ⚠️ **Protocol Non-Compliance**
  - **Analysis**: `TypeError`s are occurring within `SettlementSystem._execute_withdrawal` because it is being called with agent objects that do not fully conform to the `IFinancialAgent` protocol. The method has complex fallback logic for various legacy agent types, but this is fragile. An agent might have a `withdraw` method but not support the `currency` keyword argument, causing a `TypeError`.
  - **Evidence**: The intricate series of `isinstance` checks and fallbacks in `simulation/systems/settlement_system.py:L347-414` is a clear indicator of this problem. It attempts to call methods like `get_balance(currency)`, `.assets`, and `withdraw(amount, currency=currency)`, any of which can fail if the agent object's interface is not what is expected.
  - **Fix Recommendation**: Mandate and enforce full compliance with the `IFinancialAgent` protocol for any agent participating in transactions. Refactor all legacy agent classes (`Firm`, `Household`, etc.) to implement the required methods (`get_balance`, `deposit`, `withdraw`) with the correct signatures, including the `currency` parameter.

- **Symptom 4: Housing Test Protocol Mismatch**
  - **Status**: ⚠️ **Protocol Non-Compliance**
  - **Analysis**: An integration test for housing transactions is failing because the real `Household` agent does not fully implement the `IPropertyOwner` protocol. The `HousingTransactionHandler` attempts to call a method like `remove_property` on the seller (a `Household` instance), which is missing, leading to an `AttributeError`.
  - **Evidence**: `tests/test_wo_4_1_protocols.py` passes its checks by using a `MockAgent` that is explicitly given the required methods like `add_property` and `remove_property` (`L26-31`). This proves the handler's expectations. The failure in a real test means the `Household` class lacks these methods.
  - **Fix Recommendation**: Modify the `Household` class to correctly and completely implement all methods and attributes required by the `IPropertyOwner`, `IResident`, and `IMortgageBorrower` protocols.

- **Symptom 5: Agent ID is `None` during Settlement**
  - **Status**: ❌ **Data Integrity Error**
  - **Analysis**: Transactions are failing within `SettlementSystem` because agents are being created or passed in with their `id` attribute set to `None`. This causes a fatal error when the system tries to use the ID for logging or as a dictionary key.
  - **Evidence**: The recent addition of defensive guards in `SettlementSystem` to check for `None` IDs (`L525-534`, `L700-L707`) is strong evidence of this recurring problem. A test is likely failing because it's triggering a code path that still lacks this protection.
  - **Fix Recommendation**: Conduct a full codebase audit to ensure no agent is ever instantiated without a valid ID. Strengthen all functions that accept an agent object by adding a non-null assertion for `agent.id` at the entry point.

### Failure 6 & 7: Fragile Atomic Logic and State Leaks

These failures highlight risks in complex, multi-step operations that can leave the simulation in an inconsistent state.

- **Symptom 6: Inheritance Process Leaks Portfolio Assets**
  - **Status**: ⚠️ **State Inconsistency / Leak**
  - **Analysis**: During inheritance, portfolios (stocks, bonds) are being lost. This occurs when `execute_settlement` cannot find a valid recipient for the deceased's portfolio. The logic requires the heir (e.g., another `Household`) to implement `IPortfolioHandler`. If the heir is not compliant, the portfolio is never transferred, and `verify_and_close` later flags it as a "leak".
  - **Evidence**: `simulation/systems/settlement_system.py:L149-174` shows the portfolio transfer logic, which hinges on the recipient implementing `IPortfolioHandler`. The warning for this specific failure is logged in `verify_and_close` at `L248-255`.
  - **Fix Recommendation**: Ensure the `Household` agent class and the `Government` agent (for escheatment cases) both correctly implement the `IPortfolioHandler` protocol, enabling them to inherit portfolios.

- **Symptom 7: Atomic Transaction Rollback Failure**
  - **Status**: ⚠️ **State Inconsistency / Leak**
  - **Analysis**: The `settle_atomic` method, designed for one-to-many payments, has a fragile rollback mechanism. If a deposit to one of the recipients fails, it tries to reverse the prior deposits by calling `withdraw`. This can fail if a recipient has already moved the funds, leading to a `SETTLEMENT_FATAL` error and an inconsistent state where money has effectively been duplicated.
  - **Evidence**: The rollback logic is located in `simulation/systems/settlement_system.py:L488-504`. The `except` block logs a `CRITICAL` error if the compensating `withdraw` call fails, demonstrating the fragility of the mechanism.
  - **Fix Recommendation**: For a robust solution, implement a two-phase commit system where funds are held in a temporary state and only finalized once all parties confirm readiness. As a simpler, immediate fix, prevent agents from accessing funds received as part of an atomic batch until the entire operation is successfully completed.
