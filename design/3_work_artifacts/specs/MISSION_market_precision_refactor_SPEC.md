# Mission Guide: Market Precision Refactor (Integer Math)

## 1. Objectives (TD-MKT-FLOAT-MATCH)
- **Zero-Sum Integrity**: Eliminate all `float` drift in the matching engine.
- **Integer Transition**: Refactor price discovery and execution logic to use absolute integer pennies.
- **Rounding Protocol**: Implement deterministic rounding rules (e.g., Round-to-Floor for buyers, Remainder-to-Bank/Market-Maker).

## 2. Reference Context (MUST READ)
### Primary Target
- [matching_engine.py](../../../simulation/markets/matching_engine.py)

### Secondary Context (Protocols & Integration)
- [finance/api.py](../../../modules/finance/api.py) (ISettlementSystem, CurrencyCode)
- [order_book_market.py](../../../simulation/markets/order_book_market.py) (Calling logic)
- [TECH_DEBT_LEDGER.md](../../2_operations/ledgers/TECH_DEBT_LEDGER.md) (Detailed debt description)

## 3. Implementation Roadmap
### Phase 1: Mathematical Design
- Analyze current execution paths in `MatchingEngine.match()`.
- Define the integer-based weighted average price formula.
- Design the "Residual Penny" collection mechanism to maintain Zero-Sum.

### Phase 2: Implementation Spec
- Draft the method signatures and internal logic changes for Jules.
- Explicitly list which helper functions (e.g., `round_to_pennies`) must be used.

### Phase 3: Verification Logic
- Design a test scenario with millions of micro-transactions to verify that the total money delta is exactly 0.

## 4. Success Criteria
- No floating point arithmetic in the critical execution path.
- Pass `test_market_zero_sum_integrity.py` (to be created/updated).
