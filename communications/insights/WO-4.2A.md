# WO-4.2A Wallet Abstraction Insights

## Technical Debt & Observations

1.  **SettlementSystem Central Bank Detection**:
    The `SettlementSystem` identifies the Central Bank via `agent.__class__.__name__ == "CentralBank"` or `str(agent.id) == "CENTRAL_BANK"`. This loose coupling facilitates mocking (as seen in `trace_leak.py`) but relies on string magic which can be fragile.

2.  **Audit Log Semantics**:
    The `SettlementSystem.create_and_transfer` method (used for Minting) deposits funds into the recipient's wallet but does *not* withdraw from the Central Bank's wallet. This means the Global Wallet Audit Log's sum represents the **Net Money Supply** (Total Assets in circulation), rather than a strict zero-sum ledger including Central Bank liabilities.
    *   **Implication**: `trace_leak.py` must account for "Authorized Creation" events when verifying the log. Zero-sum integrity holds true for all *transfers* between non-CB agents.

3.  **Legacy Asset Properties**:
    Agents (`Household`, `Firm`, `Government`) still expose an `assets` property returning a dictionary. This is maintained for compatibility but delegates reads to `Wallet.get_all_balances()`. While functional, this retains an API surface area that encourages dictionary-like thinking. Future refactoring should encourage using `wallet` methods directly.

4.  **Static vs Runtime Verification**:
    The previous `trace_leak.py` used static AST analysis. The new version runs a simulation scenario. This is more effective for verifying logic but requires keeping the mock agents aligned with real agent interfaces.

## Verification Status
- `trace_leak.py` passes all zero-sum integrity checks, confirming that transfers are balanced and minting/burning is accounted for.
- `Wallet` class correctly prevents unauthorized negative balances (except for Central Bank).
