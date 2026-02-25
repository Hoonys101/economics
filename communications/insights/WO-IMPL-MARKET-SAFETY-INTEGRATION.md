# Implementation Specification: Market Safety Final Integration (WO-SPEC-MARKET-SAFETY-INTEGRATION)

## 1. 🚨 Pre-Implementation Risk Analysis (Audit Findings)

Before writing any code, Jules must be aware of the following architectural landmines identified during the pre-flight check:

1.  **High Risk to Existing Tests (`TESTING_STABILITY.md`)**:
    Modifying the `OrderBookMarket` constructor `__init__` will break **every single instantiation** of this class across the entire `tests/` directory. You MUST perform a global search (`grep`) for `OrderBookMarket(` and update all test initializations.
    *Mitigation*: Use `enforcer=MagicMock(spec=IPriceLimitEnforcer)` and `circuit_breaker=MagicMock(spec=IIndexCircuitBreaker)` to satisfy the new signature while strictly adhering to protocol-based mocking rules.
2.  **Circular Import Risk**:
    `OrderBookMarket` must NOT import concrete classes of the safety engines. It must strictly import `IPriceLimitEnforcer` and `IIndexCircuitBreaker` from their respective pure `api.py` protocol files (e.g., `modules.market.api` or `modules.finance.api`).
3.  **Registry Coupling in Initializer**:
    The `Initializer` should not hardcode the policy configurations. It must instantiate the `MarketSafetyPolicyManager` and register it with the `IGlobalRegistry` (or `IConfigurationRegistry`) to allow for dynamic, cross-system updates.
4.  **Strict SRP Enforcement**:
    `OrderBookMarket` must be completely stripped of any internal logic calculating volatility or tracking halt ticks. It is now a pure consumer of the boolean results from the injected engines.

---

## 2. Target Files & Changes Required

### Target 1: `modules/market/order_book_market.py` (or equivalent location)
- **Action**: Refactor `OrderBookMarket` to consume injected safety protocols.
- **Changes**:
  1.  **Imports**: Import `IPriceLimitEnforcer` and `IIndexCircuitBreaker` from the appropriate `api.py`.
  2.  **Constructor (`__init__`)**:
      ```python
      def __init__(
          self,
          market_id: str,
          # ... existing parameters ...
          enforcer: Optional[IPriceLimitEnforcer] = None,
          circuit_breaker: Optional[IIndexCircuitBreaker] = None
      ):
          self.market_id = market_id
          self.enforcer = enforcer
          self.circuit_breaker = circuit_breaker
          # ... existing initialization ...
      ```
  3.  **State Clean-up**: Completely remove legacy fields `self._circuit_breaker`, `self._halt_end_tick`, and `self._circuit_breaker_active`.
  4.  **Order Validation (`place_order`)**:
      At the very beginning of the `place_order` (or equivalent `submit_order`) method, inject the gateway checks:
      ```python
      # Pseudo-code logic for place_order
      def place_order(self, order: Order) -> OrderResult:
          # 1. Market Halt Check
          if self.circuit_breaker and self.circuit_breaker.is_halted(self.market_id):
              # Reject or queue based on system rules (return standard rejection DTO/Enum)
              return OrderResult.REJECTED_MARKET_HALTED
          
          # 2. Price Limit Check
          if self.enforcer and not self.enforcer.is_order_valid(order):
              return OrderResult.REJECTED_PRICE_LIMIT
          
          # 3. Proceed with legacy matching logic...
      ```

### Target 2: `modules/system/initializer.py`
- **Action**: Orchestrate and inject the safety components during system startup.
- **Changes**:
  1.  In the `_init_markets` phase (or equivalent orchestration method), instantiate the concrete safety engines (`PriceLimitEnforcer`, `IndexCircuitBreaker`).
  2.  Instantiate the `MarketSafetyPolicyManager`.
  3.  Register the manager (or its configurations) into the `IGlobalRegistry` so the Cockpit/Government can mutate limits dynamically.
  4.  Pass the initialized enforcer and circuit breaker into the constructors of the actual `OrderBookMarket` instances (e.g., Stock Market, Goods Market).

### Target 3: `tests/` Directory (Global Update)
- **Action**: Fix all broken test instantiations.
- **Changes**:
  1.  Search for all `OrderBookMarket` instantiations.
  2.  Update signatures. Example:
      ```python
      mock_enforcer = MagicMock(spec=IPriceLimitEnforcer)
      mock_enforcer.is_order_valid.return_value = True
      
      mock_cb = MagicMock(spec=IIndexCircuitBreaker)
      mock_cb.is_halted.return_value = False
      
      market = OrderBookMarket(
          market_id="TEST_MARKET",
          enforcer=mock_enforcer,
          circuit_breaker=mock_cb
      )
      ```

---

## 3. Testing & Verification Strategy

- **New Test Cases (`test_market_safety_integration.py` or updated `test_order_book_market.py`)**:
  - *Happy Path*: Order passes through `is_order_valid == True` and `is_halted == False` and is successfully added to the book.
  - *Edge Case 1 (Halted)*: When `circuit_breaker.is_halted()` returns `True`, assert the order is rejected immediately without touching the internal matching engine.
  - *Edge Case 2 (Limit Violation)*: When `enforcer.is_order_valid()` returns `False`, assert the order is rejected.
- **Existing Test Impact**: Every unit test invoking `OrderBookMarket` directly will fail `TypeError: __init__() missing required positional arguments` if the new parameters aren't strictly typed as `Optional` or if tests pass positional args. Keep them `Optional` but proactively update tests for hygiene.
- **Integration Check**: Run `pytest tests/` and verify that `test_order_book_market.py` and `test_safety_policy.py` pass cleanly.

---

## 4. 🚨 MANDATORY REPORTING INSTRUCTION (For Jules)

**ATTENTION JULES:**
As a strict requirement for this mission's completion, you **MUST** create a new, isolated insight report file at the following path:
`communications/insights/WO-SPEC-MARKET-SAFETY-INTEGRATION.md`

Do **NOT** append your findings to `manual.md`, `HANDOVER.md`, or any existing files.
Your report must contain:
1. **[Architectural Insights]**: Document any technical debt resolved (e.g., removal of legacy circuit breaker logic) or newly discovered issues during the registry wiring.
2. **[Regression Analysis]**: Briefly explain how many tests were affected by the `OrderBookMarket` signature change and how you applied the `TESTING_STABILITY.md` guidelines (`spec=Protocol`) to fix them.
3. **[Test Evidence]**: Copy and paste the final, successful `pytest` output block showing 100% pass rate for the affected test suite.

Failure to generate this exact file with the required contents will result in a hard failure of the assignment.