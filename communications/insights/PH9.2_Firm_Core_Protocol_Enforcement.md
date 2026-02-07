# PH9.2 Firm & Core Protocol Enforcement Report

## 1. Problem Phenomenon
- **Conflicting OrderDTO Definitions**: `OrderDTO` was defined in three different places (`modules/market/api.py`, `simulation/dtos/api.py`, `simulation/api.py`) with inconsistent fields (e.g., `currency` present in one but not others, `side` missing in some). This created ambiguity and potential type errors.
- **Protocol Bypass in Agents**:
    - `Firm` agent directly accessed `self._inventory` (a `BaseAgent` implementation detail) in methods like `liquidate_assets`, `calculate_valuation`, etc., violating the `IInventoryHandler` protocol.
    - `Household` agent bypassed encapsulation by aliasing `self._inventory = self._econ_state.inventory` in `__init__`, exposing internal state to the base class structure inappropriately.

## 2. Root Cause Analysis
- **Code Duplication**: `OrderDTO` was redefined in "public API" files (`simulation/api.py`) instead of being imported from the canonical source, leading to drift over time (e.g., Phase 33 updates applied only to one copy).
- **Inheritance vs Composition**: `Firm` inherits from `BaseAgent`, which exposes `_inventory` as a protected attribute. Developers naturally used it directly instead of the public protocol methods (`get_quantity`, `get_all_items`).
- **Legacy Patterns**: The `Household` alias was a legacy workaround to make `BaseAgent` methods work with `EconStateDTO`, but it broke the "pure state" abstraction.

## 3. Solution Implementation Details

### 3.1 OrderDTO Standardization
- **Central Source of Truth**: Established `modules.market.api.OrderDTO` as the canonical definition (aliased as `simulation.models.Order`).
- **Unified Imports**: Replaced local class definitions in `simulation/dtos/api.py` and `simulation/api.py` with aliases to `simulation.models.Order`.
- **Field Updates**: Added `currency: CurrencyCode = DEFAULT_CURRENCY` to the canonical `OrderDTO` to support Phase 33 requirements and standardize usage.

### 3.2 Firm Protocol Enforcement
- Refactored `Firm` methods (`liquidate_assets`, `get_agent_data`, `calculate_valuation`, `get_financial_snapshot`, `generate_transactions`, `clone`) to use `IInventoryHandler` methods:
    - Replaced `self._inventory.keys()` with `self.get_all_items().keys()`.
    - Replaced `self._inventory.items()` with `self.get_all_items().items()`.
    - Replaced `self._inventory.copy()` with `self.get_all_items()`.
- This ensures `Firm` logic is decoupled from the underlying storage mechanism of inventory.

### 3.3 Household Protocol Enforcement
- Removed the `self._inventory = self._econ_state.inventory` alias in `Household.__init__`.
- Updated `make_decision` to pass `self.get_all_items()` to the social component instead of raw state access.
- Confirmed `Household` overrides all `IInventoryHandler` methods, making the `BaseAgent._inventory` attribute effectively unused and irrelevant, which is cleaner.

## 4. Lessons Learned & Technical Debt
- **DTO Centralization**: DTOs should never be redefined for "convenience". Use imports or strictly typed aliases.
- **Protocol Usage**: When inheriting from a base class that implements a protocol (like `BaseAgent` implements `IInventoryHandler`), subclasses should strictly adhere to the protocol interface even for internal logic where possible, to facilitate future refactoring (e.g., changing storage backend).
- **Redundancy**: `OrderDTO` now contains both `currency` and `monetary_amount` (Optional). `monetary_amount` is used for internal firm orders (`INVEST_...`), while `currency` is used for market orders. Future refactoring should merge these into a single consistent monetary representation.
