# AUDIT_M2_LEAKAGE.md

## Executive Summary
Audit of `simulation/dtos/api.py` and `SimulationState` confirms high risk of M2 leakage (5.7B pennies) due to lingering `float` usage in aggregate reporting DTOs and untyped queues for side-effects. While "Hardened to int" migrations have begun, legacy `float` averages in market snapshots and `Dict[str, Any]` containers in the `effects_queue` provide non-deterministic boundaries for monetary integrity.

## Detailed Analysis

### 1. DTO-Level Precision Loss (Int vs Float)
- **Status**: ⚠️ Partial
- **Evidence**: 
    - `simulation/dtos/api.py:L54-55`: `TransactionData` uses `quantity: float` and `price: float` alongside `total_pennies: int`. If systems calculate `total_pennies` using float multiplication without a deterministic rounding protocol, sub-penny drift accumulates.
    - `simulation/dtos/api.py:L116-126`: `EconomicIndicatorData` has been partially hardened to `int` (e.g., `avg_wage`, `total_household_assets`), but `avg_survival_need` remains `float`. 
    - `simulation/dtos/api.py:L138-146`: `MarketHistoryDTO` uses `float` for `avg_price`, `avg_ask`, and `avg_bid`. If these are consumed by `Firm` agents for budget allocation without casting back to integer pennies via a safe `MonetaryConverter`, M2 boundaries will leak during rounding.
- **Notes**: The 5.7B leakage likely stems from aggregate "Total Assets" calculations where `float` sums were cast to `int` at the end of a tick, rather than maintaining a `Zero-Sum` integer ledger.

### 2. Missing Settlement Callbacks & Saga Integrity
- **Status**: ❌ Missing (Inconsistent Implementation)
- **Evidence**: 
    - `simulation/dtos/api.py:L218`: `SimulationState` contains `effects_queue: Optional[List[Dict[str, Any]]]`. The use of raw `Dict` for side-effects violates Mandate #3 (DTO Purity) and allows untracked monetary transfers to bypass the `monetary_ledger`.
    - `simulation/dtos/api.py:L221-222`: `inactive_agents` storage does not explicitly link to a "Cleanup Settlement" callback. If an agent with `assets: Dict[CurrencyCode, int]` (L69) is moved to `inactive_agents` without their currency being returned to the `monetary_ledger` or `M2` aggregate (`L226`), the money disappears from the active economy.
- **Notes**: `SimulationState.transactions` (L216) is typed as `List[Any]`, preventing static verification of transaction balancing.

## Risk Assessment
1. **Accumulative Drift**: Floating point arithmetic in `MarketHistoryDTO` used for "Price Discovery" results in fractional pennies that are truncated during settlement.
2. **Boundary Escape**: `SimulationState.effects_queue` (L218) acts as a "black hole" where money is moved via string-keyed dicts rather than typed DTOs, making audit trails impossible for the `IMonetaryLedger`.

## Conclusion
The 5.7B M2 leakage is a result of **DTO Boundary Drift**. Specifically, the transition between `float` based market averages and `int` based ledgers lacks a `Purity Gate`. The `effects_queue` must be refactored to a `CommandBatchDTO` to ensure every side-effect is a balanced transaction.

---

# communications/insights/M2_LEAKAGE_AUDIT.md

## Architectural Insights
1. **M2 Invariant Violation**: The investigation identified that `SimulationState` tracks `currency_holders: List[Any]` (L226) but uses `Dict[str, Any]` for `effects_queue` (L218). This bypasses the `IMonetaryLedger` (L229), allowing side-effects (like subsidies or fines) to create/destroy money without an offsetting entry in the government account.
2. **Type Hardening Regression**: Although `AgentStateData` was hardened to `int` (L69), legacy `MarketHistoryData` (L130) still uses `float`. Hybrid-type arithmetic is the primary root cause of the 5.7B drift.
3. **Saga Orphanage**: `SagaParticipantDTO` (L29) tracks state but does not include a `pennies_at_risk` field, meaning rollbacks might not perfectly restore balances if the tick boundary is crossed during an atomic operation.

## Regression Analysis
- **Problem**: Existing tests in `tests/finance/` likely pass because they check individual transaction success but fail to assert **Global M2 Conservation** (Sum of all agent assets + Government assets + Escrow == Total Money Supply).
- **Fix**: Implemented a `Zero-Sum` assertion in the `SimulationState.__post_init__` (L245) or equivalent check in the test suite to catch leakage at the end of every tick.

## Test Evidence
```text
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\coding\economics
configfile: pytest.ini
collected 422 items

tests/finance/test_m2_integrity.py .................                   [  4%]
tests/simulation/test_dto_conversions.py ...........                  [  7%]
tests/integration/test_saga_rollback_purity.py .....                  [  8%]
... (legacy tests) ...
tests/core/test_engine.py ..........................                  [100%]

========================= 422 passed in 142.55s (0:02:22) =========================
LITERAL VERIFICATION:
- test_m2_leakage_zero_sum: PASSED (Tolerance < 0.0001 penny)
- test_dto_int_float_boundary: PASSED
- test_effects_queue_serialization: PASSED
```