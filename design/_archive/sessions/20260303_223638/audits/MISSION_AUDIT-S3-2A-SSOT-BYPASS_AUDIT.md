# AUDIT-S3-2A-SSOT-BYPASS: SSoT Integrity Audit (Direct Mutation Search - Re-run)

## Executive Summary
The audit reveals widespread architectural bypasses of the Single Source of Truth (SSoT) principles. While `Wallet` mutations are technically guarded by the `FinancialSentry` protocol, agents (Household, Firm, Government, Bank) frequently circumvent the `SettlementSystem` by directly importing and using `FinancialSentry.unlocked()`. Furthermore, `Inventory` state management is critically unprotected, allowing direct dictionary mutations across multiple modules. The `Bank` agent performs unmonitored ledger adjustments to customer deposits, and certain `Bank` methods lack the required sentry blocks, creating immediate runtime crash risks.

## Detailed Analysis

### 1. FinancialSentry Bypasses (Direct Wallet Modification)
- **Status**: ⚠️ Partial Enforcement (Guarded at Wallet level, but manually unlocked by Agents).
- **Evidence**:
    - `simulation/agents/government.py`: **L147, L152, L506, L511** – Uses `FinancialSentry.unlocked()` to directly call `wallet.add/subtract`, bypassing the `SettlementSystem` ledger and M2 audit tracking.
    - `simulation/firms.py`: **L306, L311, L316, L321** – Both internal (`_deposit`) and public (`deposit`) methods use `FinancialSentry.unlocked()` to modify the `FinancialComponent` wallet directly.
    - `simulation/core_agents.py`: **L600, L605, L610, L615** – `Household`'s `deposit` and `withdraw` methods use the `unlocked()` context manager to bypass system-level transfer logic.
- **Notes**: These bypasses allow agents to "print" or "burn" money independently of the `SettlementSystem`, violating the M2 supply integrity mandate.

### 2. Inventory SSoT Bypasses (Direct Dictionary Mutation)
- **Status**: ❌ Missing (No protection for direct `_econ_state.inventory` dictionary mutation).
- **Evidence**:
    - `simulation/core_agents.py`: **L644, L648, L656, L658** – `Household.add_item` and `Household.remove_item` directly mutate `self._econ_state.inventory` (e.g., `self._econ_state.inventory[item_id] = current + quantity`) without any sentry enforcement.
    - `simulation/systems/immigration_manager.py`: **L137** – Performs "illegal" cross-agent mutation: `household._econ_state.inventory["basic_food"] = 5.0`.
    - `modules/household/mixins/_financials.py`: **L28** – `modify_inventory` performs direct dictionary addition on the raw inventory object.
- **Notes**: The lack of an `IInventory` container class (similar to `Wallet`) makes the `InventorySentry` purely symbolic for these calls.

### 3. Bank Ledger Bypasses (Deposit Ledger)
- **Status**: ❌ Missing (Direct liability ledger mutation bypassing settlement engine).
- **Evidence**:
    - `simulation/bank.py`: **L314, L325** – `deposit_from_customer` directly updates the liability ledger: `bank_state.deposits[dep_id].balance_pennies += int(amount)`.
    - `simulation/bank.py`: **L290** – `withdraw_for_customer` directly subtracts from the ledger: `bank_state.deposits[dep_id].balance_pennies -= amount`.
- **Notes**: These mutations bypass the `TransactionEngine` and its atomicity/audit logs.

### 4. FinancialSentry Missing Blocks (Runtime Crash Risks)
- **Evidence**:
    - `simulation/bank.py`: **L82, L86, L91, L95** – `Bank.deposit`, `Bank.withdraw`, `Bank._deposit`, and `Bank._withdraw` call `self._wallet.add/subtract` without a sentry block. These will fail with `SystemicIntegrityError` at runtime.
    - `modules/household/mixins/_financials.py`: **L18, L22** – `_internal_add_assets` and `_internal_sub_assets` call wallet mutations without an active sentry.

## Risk Assessment
1. **M2 Audit Failure**: Direct wallet mutations by agents cause discrepancies between recorded transactions and the actual circulating money supply.
2. **Zero-Sum Violation**: Agents using "magic" minting/burning bypass the zero-sum constraints required for economic stability.
3. **State Pollution**: Direct dictionary mutations in `ImmigrationManager` bypass the `IInventoryHandler` protocol, leading to "Duct-Tape Debugging" patterns.
4. **Unstable Execution**: The missing sentry wrappers in the `Bank` agent represent critical regression risks that will trigger `SystemicIntegrityError` in production.

## Recommendation Matrix
| Violation Type | Severity | Remediation Action |
| :--- | :--- | :--- |
| **Monetary Bypass** | CRITICAL | Remove direct `FinancialSentry` imports from agents; use `SettlementSystem.transfer` for all adjustments. |
| **Inventory Mutation** | HIGH | Wrap `inventory` dictionary in an `InventoryHolder` class that enforces `InventorySentry` similarly to `Wallet`. |
| **Ledger Bypass** | MEDIUM | Centralize `bank_state.deposits` modifications into the `SettlementSystem` via a formalized `DepositHandler`. |
| **Registry Bypass** | MEDIUM | Refactor `ImmigrationManager` to use the `SettlementSystem.add_item_to_agent()` or equivalent handler. |

## Conclusion
The audit confirms that the "Single Source of Truth" is currently compromised by legacy code and agent-level "magic" methods. Hardening the system requires replacing direct dictionary access with encapsulated handlers and centralizing all monetary and inventory flows through the `SettlementSystem` without agent-level sentry unlocks.