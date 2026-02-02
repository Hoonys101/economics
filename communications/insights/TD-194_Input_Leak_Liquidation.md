# Insight: [TD-194] Input Leak Liquidation

## 1. Overview
This refactoring aimed to eliminate "Abstraction Leaks" where agents (`Household`, `Firm`) were accessing raw market objects (e.g., `OrderBookMarket`) via the `DecisionInputDTO.markets` dictionary during their decision-making phase. This violated the "Purity Gate" architecture, which mandates that agents should only perceive the world through sanitized DTOs (Snapshots and Signals).

## 2. Changes Implemented

### 2.1 Purity Enforcement
- **Removed `markets` from `DecisionInputDTO`**: The `markets: Dict[str, Any]` field has been removed. Any attempt to access raw markets in `make_decision` will now fail at the type checking or runtime level (if untyped).
- **Verified via `trace_leak.py`**: A static analysis script confirmed zero occurrences of `markets` attribute access or `markets.get()` calls within `make_decision` methods of `core_agents.py` and `firms.py`.

### 2.2 DTO Enhancements (`modules/system/api.py`)
- **Enhanced `MarketSignalDTO`**: Added `total_bid_quantity` and `total_ask_quantity` fields. This allows agents (specifically Firms) to calculate "Invisible Hand" signals (Excess Demand) without iterating over raw order books.
- **New Snapshot DTOs**: defined `HousingMarketSnapshotDTO`, `LoanMarketSnapshotDTO`, and `LaborMarketSnapshotDTO` as dataclasses in `modules.system.api`.
- **Integrated `MarketSnapshotDTO`**: The system-wide snapshot DTO now carries optional sub-snapshots for housing, loan, and labor markets.

### 2.3 Orchestration Updates
- **`MarketSnapshotFactory`**: Created a new factory in `simulation.orchestration.factories` responsible for:
  1. Generating `MarketSignalDTO`s (including the new quantity sums).
  2. Extracting specific market state into `Housing/Loan/Labor` snapshots.
- **`Phase1_Decision`**: Refactored to use `MarketSnapshotFactory`. It now generates a fully populated snapshot *before* creating the `DecisionInputDTO`.

### 2.4 Agent Refactoring
- **Firm (`simulation/firms.py`)**:
  - `_calculate_invisible_hand_price` now accepts `MarketSnapshotDTO`.
  - It uses `market_signals[item_id].total_bid/ask_quantity` instead of accessing raw market order books.
- **Household (`simulation/core_agents.py`)**:
  - `make_decision` no longer constructs `HousingMarketSnapshotDTO` locally.
  - It uses the pre-calculated `input_dto.market_snapshot` which now contains the housing data.

## 3. Technical Debt & Fixes
- **OrderDTO Compliance**: While running tests, we discovered `Order` instantiation in `SalesDepartment` and `DynamicPricing` logic was using legacy arguments (`order_type`, `price`) or attempting to mutate frozen DTOs.
  - **Fix**: Updated to use `side` and `price_limit`.
  - **Fix**: Used `dataclasses.replace` for modifying frozen `OrderDTO`s in dynamic pricing logic.
- **Outdated Tests**: `tests/unit/test_household_decision_engine_new.py` was failing because it expected `make_decisions` to return a tuple, but it now returns `DecisionOutputDTO`. Updated the tests to unpack the DTO correctly.

## 4. Verification
- `trace_leak.py`: **0 Leaks**.
- `tests/unit/test_firms.py`: **Passed**.
- `tests/unit/test_household_decision_engine_new.py`: **Passed**.

## 5. Conclusion
The "Purity Gate" is now strictly enforced regarding market access. Agents rely solely on `MarketSnapshotDTO` for their market perception. Future market data requirements must be exposed via DTOs/Signals in the `MarketSnapshotFactory`.
