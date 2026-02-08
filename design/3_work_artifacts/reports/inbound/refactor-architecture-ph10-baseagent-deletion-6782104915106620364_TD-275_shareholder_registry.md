# Technical Insight Report: Shareholder Registry & Dividend Optimization (TD-275)

## 1. Problem Phenomenon
- **Symptom**: The `FinanceDepartment.process_profit_distribution` method contained an `O(N*M)` loop, iterating over all households (N) for every firm (M) to distribute dividends.
- **Impact**: This caused significant performance degradation as the number of agents increased (Quadratic complexity).
- **Stack Trace**: N/A (Performance Issue).

## 2. Root Cause Analysis
- **Design Flaw**: Share ownership data was decentralized and scattered (e.g., `Household.portfolio`, `Firm.treasury_shares`).
- **Access Pattern**: To find shareholders, the system had to scan every potential shareholder (Household) to check if they owned shares of the specific firm.
- **Coupling**: Financial logic was tightly coupled with iteration over agent lists.

## 3. Solution Implementation Details
- **ShareholderRegistry Service**: Implemented a centralized `ShareholderRegistry` service (`modules/finance/shareholder_registry.py`) that maintains a `firm_id -> agent_id -> quantity` mapping (Reverse Index).
- **DTO Interaction**: Defined `ShareholderData` TypedDict and `IShareholderRegistry` Protocol in `modules/finance/api.py`.
- **Integration**:
    - `StockMarket` now delegates `update_shareholder` calls to the Registry, ensuring backward compatibility with existing TransactionHandlers.
    - `FinanceDepartment` now requests shareholders from the Registry (`get_shareholders_of_firm`), reducing complexity to `O(K)` where K is the number of actual shareholders.
    - `Firm.generate_transactions` and `Phase_FirmProductionAndSalaries` were updated to propagate the Registry instance.
- **State Management**: Added `shareholder_registry` to `SimulationState`, `WorldState`, and `TransactionContext`.

## 4. Lessons Learned & Technical Debt Identified
- **Lesson**: Centralized reverse indices are crucial for performance in many-to-many relationships (Firms <-> Shareholders).
- **Technical Debt**:
    - `StockMarket` still retains some registry-like responsibilities (checking limits, etc.). Ideally, it should be purely an exchange mechanism.
    - `FinanceDepartment` has a `retained_earnings` field that appears unused/stale.
    - `trace_tick.py` script is brittle and outdated, failing on unrelated attribute access (`tick_scheduler`), making regression testing harder.
    - `Firm.total_shares` vs Registry total might drift if not carefully managed (though Registry is now the authority for owned shares).