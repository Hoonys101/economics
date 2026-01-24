# Report: Positive Money Drift (TD-105) Investigation

## Executive Summary
The investigation has located the source of the positive money drift. The `EconomicRefluxSystem` directly injects its balance into household assets each tick without a corresponding transaction, and its balance is being populated by financial operations that lack a debiting counterpart, causing money to be created from nothing.

## Detailed Analysis

### 1. Money Injection Mechanism
- **Status**: ✅ Implemented
- **Evidence**: `simulation/systems/reflux_system.py:L48-L62`
- **Notes**: The `distribute` method in `EconomicRefluxSystem` iterates through active households and directly increases their assets by calling `agent._add_assets()`. This is an explicit "magic minting" of money, where the total amount created equals the `balance` of the reflux system at the time of distribution. The problem, therefore, lies in how the `balance` is populated.

### 2. Unbalanced Capture Source: Bank Profits
- **Status**: ✅ Implemented
- **Evidence**: `simulation/bank.py:L446-L460`
- **Notes**: The `run_tick` method in the `Bank` calculates `net_profit`. If the profit is positive, it generates a `Transaction` with `transaction_type="reflux_capture"`. Crucially, the `seller_id` (recipient) of this transaction is the `gov_agent.id`, not the `reflux_system`. This means the bank's profits are correctly transferred to the government's assets. This is a balanced transfer and **not the source of the leak**.

### 3. Unbalanced Capture Source: Infrastructure Investment
- **Status**: ⚠️ **Partially Implemented (Identified Leak)**
- **Evidence**: `simulation/agents/government.py:L563-L602`
- **Notes**: The `invest_infrastructure` method in the `Government` class is a source of money creation.
    1. If the government's assets are insufficient, it issues bonds to cover the cost. This part is balanced.
    2. It then calls `self.settlement_system.transfer(self, reflux_system, effective_cost, ...)`.
    3. The `settlement_system` is expected to debit the government and credit the `reflux_system`. However, the comment on `L575` ("*Bypass TransactionProcessor for internal transfers to prevent zero-sum drift*") and the direct call to `settlement_system.transfer` for this purpose strongly implies a flawed, non-transactional internal transfer is taking place. If the debit from the government fails or is implemented incorrectly within the settlement system (code not provided), while the credit to reflux succeeds, money is created. Given the problem description, this is a highly probable source of the leak. The cost, `effective_cost`, if it were a constant value (e.g., from config), could explain the fixed drift amount.

### 4. Unbalanced Capture Source: Firm Investments
- **Status**: ✅ Implemented (Potential Leak)
- **Evidence**: `simulation/components/finance_department.py:L452-L483`
- **Notes**: The methods `invest_in_automation`, `invest_in_rd`, and `invest_in_capex` in the `FinanceDepartment` use the same pattern as the government's infrastructure investment: `settlement_system.transfer(self.firm, reflux_system, amount, ...)`. Similar to the government, if the `settlement_system` fails to properly debit the firm while crediting the `reflux_system`, money is created. The comment "Prevent money destruction. Investment requires RefluxSystem" (`L468`) suggests this mechanism was intentionally designed to ensure money flows to reflux, but the debit side may be flawed.

## Risk Assessment
The core issue is the use of direct asset manipulation (`_add_assets`) and non-transactional settlement transfers (`settlement_system.transfer`) instead of the standard, balanced `TransactionProcessor`. The `EconomicRefluxSystem` is designed to be a sink for economic activity, but its `distribute` function reinjects this money without it ever having been properly debited from the original spenders (firms, government), leading to consistent money supply inflation.

## Conclusion
The positive money drift originates from investment-style expenditures (`invest_infrastructure`, `invest_in_rd`, etc.) being captured by the `EconomicRefluxSystem` without a corresponding, guaranteed debit from the investing agent's assets. The captured funds are then injected directly into households' assets via the `RefluxSystem.distribute` method. The fix is to ensure that all transfers into the `RefluxSystem` are processed as standard, two-sided transactions that debit the sender and credit the receiver, eliminating the possibility of an unbalanced credit.
