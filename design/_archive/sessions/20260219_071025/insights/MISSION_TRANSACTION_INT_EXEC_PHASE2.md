# MISSION: Implement Specialized Transaction Handlers (Goods, Labor, etc.)

## 1. Architectural Insights

### Technical Debt Identified
- **TransactionManager vs TransactionProcessor**: The codebase currently has both `TransactionManager` (new, intended SSoT) and `TransactionProcessor` (legacy/alternative). `TransactionManager` contained inline logic for major transaction types (Goods, Labor), violating separation of concerns and making it a "God Class".
- **Registry Inconsistency**: The `Registry` class had disabled logic for `goods` inventory updates, relying on `TransactionProcessor`'s handler to do it. However, `TransactionManager` relies on `Registry` to handle side effects. This created a gap where using `TransactionManager` would result in no inventory updates for goods.

### Architectural Decisions
- **Specialized Handlers**: Extracted `GoodsTransactionHandler` and `LaborTransactionHandler` into `modules/finance/transaction/handlers/`. These handlers implement the `ISpecializedTransactionHandler` protocol.
- **Protocol Purity**: Introduced `ISolvent` and `ITaxCollector` protocols in `modules/finance/transaction/handlers/protocols.py` to replace `hasattr` checks, adhering to strict typing guardrails.
- **Registry Restoration**: Restored the inventory update logic in `Registry._handle_goods_registry` to ensure `TransactionManager` correctly updates state after financial settlement. This restores the "Logic Separation" principle where Handlers do Finance and Registry does State.
- **Dynamic Dispatch**: `TransactionManager` now dynamically dispatches to handlers based on transaction type, allowing for easier extensibility.

## 2. Test Evidence

### New Handlers Test (`tests/unit/test_transaction_handlers.py`)
```
tests/unit/test_transaction_handlers.py::TestGoodsTransactionHandler::test_goods_escrow_fail PASSED [ 20%]
tests/unit/test_transaction_handlers.py::TestGoodsTransactionHandler::test_goods_success PASSED [ 40%]
tests/unit/test_transaction_handlers.py::TestGoodsTransactionHandler::test_goods_trade_fail_rollback PASSED [ 60%]
tests/unit/test_transaction_handlers.py::TestLaborTransactionHandler::test_labor_firm_tax_payer PASSED [ 80%]
tests/unit/test_transaction_handlers.py::TestLaborTransactionHandler::test_labor_household_tax_payer PASSED [100%]
```

### Regression Test (`tests/unit/test_transaction_processor.py`)
```
tests/unit/test_transaction_processor.py::test_transaction_processor_dispatch_to_handler PASSED [ 20%]
tests/unit/test_transaction_processor.py::test_transaction_processor_ignores_credit_creation PASSED [ 40%]
tests/unit/test_transaction_processor.py::test_goods_handler_uses_atomic_settlement PASSED [ 60%]
tests/unit/test_transaction_processor.py::test_public_manager_routing PASSED [ 80%]
tests/unit/test_transaction_processor.py::test_transaction_processor_dispatches_housing PASSED [100%]
```
