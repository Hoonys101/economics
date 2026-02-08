# Structural Audit Report: God Class & Abstraction Leak

**Task ID:** audit_structural_god_class_abstraction
**Date:** 2024-05-22
**Auditor:** Jules

## 1. Executive Summary
This audit identified significant structural issues in the `Household` class, which has grown into a "God Class". Additionally, abstraction leaks were found where decision logic accesses raw market objects instead of DTOs. A deviation from the standard simulation sequence was also noted regarding the Bankruptcy phase.

## 2. God Class Detection
Scan threshold: 800 lines.

### 2.1. Household (Critical)
- **File:** `simulation/core_agents.py`
- **Lines:** 977
- **Analysis:**
  - The class acts as a massive Facade for `BioComponent`, `EconComponent`, and `SocialComponent`.
  - A significant portion of the file (approx. 300+ lines) is dedicated to property delegation (getters/setters) to these internal components.
  - This violates the Single Responsibility Principle and makes the class difficult to maintain and test.
- **Recommendation:**
  - Remove property delegations where possible and expose components directly (e.g., `household.econ.assets` instead of `household.assets`), or use a more dynamic proxy mechanism (though explicit is better).
  - Move "Agent Data" adapter logic (`get_agent_data`, `create_state_dto`) to a dedicated `HouseholdAdapter` or `Serializer`.

### 2.2. TestFirmDecisionEngine (Warning)
- **File:** `tests/unit/test_firm_decision_engine_new.py`
- **Lines:** 828
- **Analysis:**
  - The test file is large, indicating that `FirmDecisionEngine` has a complex surface area.
  - While test files are allowed to be larger, it suggests that the unit under test might be doing too much.

## 3. Abstraction Leaks

### 3.1. Direct Market Access in Decision Logic
- **Location:** `modules/household/decision_unit.py` (Delegated from `Household`)
- **Leak:**
  ```python
  if hasattr(housing_market_obj, "sell_orders"):
      for item_id, sell_orders in housing_market_obj.sell_orders.items():
  ```
- **Analysis:**
  - The decision logic directly inspects `sell_orders` of the `OrderBookMarket` object.
  - This bypasses the `MarketSnapshotDTO` / `MarketSignalDTO` abstraction layer.
  - It creates a tight coupling between the decision engine and the specific implementation of the market (`OrderBookMarket`).
- **Recommendation:**
  - Populate `MarketSnapshotDTO` with necessary housing market data (e.g., `best_ask_price`, `available_inventory`) in `Phase1_Decision` or `prepare_market_data`.
  - Update `DecisionUnit` to consume `MarketSnapshotDTO`.

### 3.2. Phase 1 Execution Arguments
- **Location:** `simulation/orchestration/phases.py`
- **Leak:** `Firm.make_decision` and `Household.make_decision` receive `state.markets` (Dict of objects) alongside DTOs.
- **Analysis:**
  - While the method signatures use `Dict[str, Any]` or `Dict[str, IMarket]`, passing the live market objects allows agents to potentially call mutable methods (state change) during the decision phase.
- **Recommendation:**
  - Ideally, pass only `MarketSnapshotDTO` or a Read-Only Interface of the market.

## 4. Sequence Violations

### 4.1. Bankruptcy Phase Positioning
- **Standard Sequence:** Decisions -> Matching -> Transactions -> Lifecycle
- **Observed Sequence:** Decisions -> **Bankruptcy** -> **SystemicLiquidation** -> Matching -> Transactions -> Consumption
- **Analysis:**
  - `Phase_Bankruptcy` (Lifecycle) occurs *before* Matching.
  - This appears to be an intentional design to allow for "Same-Tick Liquidation" (bankrupt firms dump assets -> matched in `Phase2_Matching`).
  - However, it technically violates the "Lifecycle at the end" standard.
- **Recommendation:**
  - Document this exception explicitly in `ARCH_SEQUENCING.md` as "Fast-Fail Liquidation Pattern".
  - Or, if strict adherence is required, move Bankruptcy to the end, meaning liquidation happens in the *next* tick.

## 5. Conclusion
Immediate refactoring is recommended for `Household` to reduce its size and complexity. The abstraction leak in `DecisionUnit` regarding housing market access should be plugged to prevent future regressions where agents might manipulate markets during decision time.