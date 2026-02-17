# Mission Guide: Transaction Logic Unification

## 1. Objectives (TD-PROC-TRANS-DUP)
- **Eliminate Redundancy**: Deprecate legacy `TransactionManager` and move all logic to `TransactionProcessor`.
- **Unify Settlement Path**: Ensure there is ONE SSoT for how money and goods change hands.
- **Safety Parity**: Ensure the new processor has all the safety checks (e.g., double-spending protection) present in the legacy manager.

## 2. Reference Context (MUST READ)
### Targets
- [transaction_manager.py](../../../simulation/systems/transaction_manager.py) (Legacy)
- [transaction_processor.py](../../../simulation/systems/transaction_processor.py) (Target)

### Secondary Context
- [matching_engine.py](../../../simulation/markets/matching_engine.py) (Generator of transactions)
- [finance/api.py](../../../modules/finance/api.py) (Settlement interfaces)

## 3. Implementation Roadmap
### Phase 1: Gap Analysis
- Comparison of logic between `manager` and `processor`.
- Identify any unique features in legacy that need migration.

### Phase 2: Implementation Spec
- Plan the redirection of all callers from `TransactionManager` to `TransactionProcessor`.
- Mark legacy methods as deprecated or remove if safe.

### Phase 3: Cleanup
- Remove the legacy `transaction_manager.py` file once 100% migrated.

## 4. Success Criteria
- Zero occurrences of `TransactionManager` in the codebase.
- Pass all unit and integration tests related to market settlement and agent wallets.
- Verified zero-sum integrity in settlement.
