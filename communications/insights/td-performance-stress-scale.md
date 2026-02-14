# Insight Report: Optimize Bank Stress Scan (O(N) -> O(1))

## Architectural Insights

### 1. Reverse Index Implementation
To address the O(N) performance bottleneck in `FORCE_WITHDRAW_ALL`, a reverse index `Bank -> List[Depositors]` was introduced in the `SettlementSystem`. This transforms the complexity of finding account holders for a bank run simulation from linear (scanning all agents) to constant/proportional (accessing a cached list).

### 2. Synchronization Strategy
The index is synchronized at three key lifecycle events:
- **Account Creation**: When a loan is booked (via `FinanceSystem`) or a manual deposit occurs (via `Bank`), `SettlementSystem.register_account` is called.
- **Account Closure**: When an agent is liquidated (via `AgentLifecycleManager`), `SettlementSystem.remove_agent_from_all_accounts` is called.
- **Index Storage**: The index uses `Dict[BankID, Set[AgentID]]` for efficient O(1) insertions and lookups, while also maintaining a forward index `Dict[AgentID, Set[BankID]]` to enable fast O(1) removal of agents upon death.

### 3. Protocol Updates
The `ISettlementSystem` protocol was updated to formally include `register_account`, `deregister_account`, `get_account_holders`, and `remove_agent_from_all_accounts`, ensuring type safety and architectural compliance.

## Test Evidence

### Manual Verification Script (`test_settlement_index.py`)
A dedicated verification script was created to test the index logic in isolation.

**Script Output:**
```
Holders 101: [1, 2]
Holders 102: [3]
Holders 103: []
Holders 101 after deregister 1: [2]
Holders 101 before removal: [2, 4]
Holders 101 after removal: [2]
Verification Passed!
```

### Integration Logic Verification
- `modules/system/services/command_service.py` was updated to use `settlement_system.get_account_holders(bank_id)` instead of iterating `agent_registry.get_all_agents()`.
- `modules/finance/system.py` and `simulation/bank.py` were updated to call `register_account` on deposit creation.
- `simulation/systems/lifecycle_manager.py` was updated to call `remove_agent_from_all_accounts` on agent liquidation.

These changes ensure the index remains accurate throughout the simulation lifecycle.
