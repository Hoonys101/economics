# Insight: Implementing Financial Fortress (SSoT)

## 1. Overview
The "Financial Fortress" mission aimed to enforce the SettlementSystem as the Single Source of Truth (SSoT) for all monetary assets in the simulation. This involved removing direct wallet mutations (`deposit`/`withdraw`) from Agents (`Household`, `Firm`) and refactoring the `FinanceSystem` to eliminate its parallel ledger of reserves/balances.

## 2. Key Architectural Changes

### 2.1. Agent Wallet Lockdown
- **Deprecated:** Public `deposit(amount)` and `withdraw(amount)` methods on `Household`, `Firm`, and `Bank` now raise `NotImplementedError`.
- **Internalized:** Renamed to `_deposit(amount)` and `_withdraw(amount)`. These are strictly for internal use by the `SettlementSystem`.
- **Load State Safety:** The `load_state` method no longer hydrates financial assets directly from DTOs. This prevents "magic money" injection during restoration or instantiation.

### 2.2. SettlementSystem as SSoT
- **Interface Update:** `ISettlementSystem` now includes `get_balance(agent_id, currency)` and `transfer(...)`.
- **Dependency Injection:** `SettlementSystem` now requires `AgentRegistry` to look up agents for balance checks (resolving `AgentID` -> `Agent` instance). This was injected via `SimulationInitializer`.
- **Mocking:** A `MockSettlementSystem` was introduced to facilitate robust unit testing without spinning up the full engine.

### 2.3. FinanceSystem Refactoring
- **Stateless Orchestrator:** The `FinanceSystem` no longer maintains persistent state for Bank Reserves or Government Treasury Balance in its `self.ledger`.
- **Sync-on-Demand:** A new helper `_sync_ledger_balances()` pulls real-time balances from `SettlementSystem` at the start of critical methods (`issue_treasury_bonds`, `request_bailout_loan`).
- **Dual-Write Elimination:** Manual updates to `ledger.banks[].reserves` inside transaction methods were removed. The system now relies on `settlement_system.transfer` to move funds, and the subsequent sync reflects this reality.

### 2.4. Agent Factory & Bootstrapper
- **Genesis & Immigration:** `HouseholdFactory` and `Bootstrapper` were updated to use `SettlementSystem` (specifically `create_and_transfer` or `transfer`) to fund new agents, ensuring zero-sum integrity from the very first tick.
- **Direct Injection Removed:** The fallback logic that used `firm.deposit` was removed.

## 3. Technical Debt & Risks

### 3.1. `IFinancialEntity` Deprecation
The protocol `IFinancialEntity` still defines `deposit`/`withdraw`. Since we updated agents to raise errors on these, strict adherence to this protocol is technically broken for consumers who expect it to work. We rely on consumers updating to `IFinancialAgent` or `SettlementSystem`. Ideally, `IFinancialEntity` should be fully removed in a future cleanup.

### 3.2. Mocking Complexity
The widespread changes required significant updates to mocks (`MockAgent`, `MockBank`). Future changes to `SettlementSystem` will require careful maintenance of these mocks to ensure tests remain valid.

### 3.3. Dependency Injection Timing
Injecting `AgentRegistry` into `SettlementSystem` happens post-init in `SimulationInitializer` due to circular dependency/creation order. A cleaner DI container or phase-based initialization would be more robust.

## 4. Conclusion
The implementation successfully centralizes financial authority. Agents are no longer "banks of themselves," and the `FinanceSystem` is now a true orchestrator rather than a parallel state holder. This significantly improves the auditability and integrity of the economic simulation.
