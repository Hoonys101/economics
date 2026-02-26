I will now perform a full audit of `OrderBookMarket` and its sub-components to identify all `config_module` dependencies and propose a standardized `MarketConfigDTO` structure.

# Technical Report: OrderBookMarket Configuration Audit (WO-AUDIT-MARKET-CONFIG)

## Executive Summary
This audit provides a comprehensive analysis of configuration dependencies within `OrderBookMarket` and its sub-components (`MatchingEngine`, `PriceLimitEnforcer`). The current architecture exhibits "Config Leakage," where raw `config_module` attributes are accessed alongside typed DTOs. This report identifies all such dependencies and proposes a unified `MarketConfigDTO` to enforce Protocol Purity and improve test isolation.

## Detailed Analysis

### 1. OrderBookMarket (Direct Config Access)
- **Status**: ⚠️ Partial (Legacy `getattr` usage)
- **Evidence**: `order_book_market.py:L223` shows `window_size = getattr(self.config_module, "PRICE_VOLATILITY_WINDOW_TICKS", 20)`.
- **Notes**: The market stores the entire `config_module` primarily for this single telemetry parameter. This creates a high-coupling surface area for a low-complexity requirement.

### 2. OrderBookMatchingEngine (Hardcoded Logic)
- **Status**: ❌ Missing (Configurable parameters are currently hardcoded)
- **Evidence**: 
    - `matching_engine.py:L45`: `perception = skill * (1.0 + 0.1 * education)` uses a hardcoded `0.1` weight.
    - `matching_engine.py:L288`: `trade_price_pennies = (b_wrapper.dto.price_pennies + s_wrapper.dto.price_pennies) // 2` hardcodes the Midpoint rule for commodities.
    - `matching_engine.py:L285`: `trade_price_pennies = b_wrapper.dto.price_pennies` hardcodes the Bid side priority for labor.
- **Notes**: These values should be externalized to `MarketConfigDTO` to allow for "Labor Market Shocks" or "Bargaining Power Shifts" in future scenarios without modifying the stateless engine logic.

### 3. Initialization Infrastructure (Constants Injection)
- **Status**: ⚠️ Partial (Attributes extracted but not DTO-ified)
- **Evidence**: `initializer.py:L335, L348, L539` accesses `config.GOODS`, `config.NUM_HOUSING_UNITS`, `config.INITIAL_PROPERTY_VALUE`, and `config.INITIAL_RENT_PRICE`.
- **Notes**: These constants are used to set the initial state but are not currently bundled into a shareable `MarketConfigDTO` for downstream consumers (like the `HousingService`).

## Proposed MarketConfigDTO Additions

| Field Name | Type | Source / Usage | Recommended Default |
| :--- | :--- | :--- | :--- |
| `price_volatility_window` | `int` | `OrderBookMarket.match_orders` | `20` |
| `labor_education_weight` | `float` | `MatchingEngine._calculate_labor_utility` | `0.1` |
| `commodity_matching_mode` | `str` | `MatchingEngine._match_item` (MIDPOINT/BID/ASK) | `'MIDPOINT'` |
| `labor_matching_mode` | `str` | `MatchingEngine._match_labor_utility` | `'BID'` |
| `stock_market_enabled` | `bool` | `initializer.py` (Conditional setup) | `False` |
| `initial_property_value` | `int` | `initializer.py` (Housing setup) | `None` |
| `initial_rent_price` | `int` | `initializer.py` (Housing setup) | `None` |

## Risk Assessment
- **Technical Debt**: `TD-CONFIG-HARDCODED-MAJORS` and `TD-WAVE3-MATCH-REWRITE` are directly related to the hardcoded coefficients identified in `MatchingEngine`. 
- **Integrity Risk**: Continued use of `getattr` on `config_module` risks silent failures or logic drift if naming conventions in `economy_params.yaml` change without updating the internal market code.

## Conclusion
The audit confirms that `OrderBookMarket` should be decoupled from the raw `config_module`. By expanding the existing `MarketConfigDTO` (defined in `modules/market/api.pyi`) to include the proposed fields, we can move towards a more robust, injectable architecture that supports dynamic scenario adjustments while maintaining Zero-Sum integrity and Penny Standard precision.

---

# [Architectural Insight] OrderBookMarket Configuration Audit (WO-AUDIT-MARKET-CONFIG)

## 1. Architectural Insights
- **Config Leakage**: `OrderBookMarket` still accepts a raw `config_module` primarily to access `PRICE_VOLATILITY_WINDOW_TICKS`. This violates the DTO Purity principle as the market should receive a typed `MarketConfigDTO`.
- **Hardcoded Matching Logic**: The `OrderBookMatchingEngine` contains hardcoded coefficients for labor utility calculations (`0.1` for education weight) and price determination (`// 2` for midpoint matching). These should be externalized to a configuration DTO to allow for scenario-based tuning and to prevent logic drift.
- **Inconsistent Initialization**: While safety features (Price Limits, Circuit Breakers) have transitioned to dedicated Config DTOs, core market behavior remains tethered to legacy global config attributes, creating a "mixed-mode" dependency that complicates unit testing.

## 2. Regression Analysis
- This audit identifies several "Identified" tech debt items in `TECH_DEBT_LEDGER.md` (e.g., `TD-CONFIG-HARDCODED-MAJORS`) that can be resolved by expanding `MarketConfigDTO`.
- The audit confirms that all current market components strictly adhere to the Penny Standard (Integer Math), which must be preserved in any new DTO implementation.

## 3. Test Evidence
Static analysis of `simulation/markets/order_book_market.py`, `simulation/markets/matching_engine.py`, and `simulation/initialization/initializer.py` confirms the following attribute dependencies:
- `config_module.PRICE_VOLATILITY_WINDOW_TICKS` (Used in `match_orders` for telemetry deque window)
- `config_module.GOODS` (Used in `initializer` for market registry)
- `config_module.STOCK_MARKET_ENABLED` (Used in `initializer` for conditional component activation)
- `config_module.INITIAL_PROPERTY_VALUE` / `INITIAL_RENT_PRICE` (Used for initial market state setup)

All identified attributes are candidates for migration to `MarketConfigDTO`.