# Technical Insight Report: Protocol Shield Hardening (TD-255)

## 1. Problem Phenomenon
The `HousingTransactionHandler` was relying on fragile `hasattr` checks to interact with Buyer and Seller agents.
- **Symptom**: Code used `hasattr(buyer, 'current_wage')` and `hasattr(buyer, 'get_balance')` to determine capabilities.
- **Risk**: This violates the Interface Segregation Principle and Protocol-Driven Architecture. It creates implicit coupling to implementation details (attribute names) rather than explicit contracts. If an agent renamed `current_wage` to `wage`, the handler would silently fail or degrade to legacy paths.
- **Stack Traces**: No crashes were observed, but the "Architectural Guardrails" flagged this as Technical Debt.

## 2. Root Cause Analysis
- **Implicit Interfaces**: The `Household` and `Firm` agents implemented financial and property capabilities but did not expose them through a unified, runtime-checkable Protocol for the Housing Market.
- **Legacy Code**: The handler contained fallback logic (`elif hasattr(...)`) to support older agent implementations that didn't strictly follow newer interfaces like `IMortgageBorrower`.

## 3. Solution Implementation Details
- **Defined `IHousingTransactionParticipant`**: Created a new `@runtime_checkable` Protocol in `modules/market/api.py`.
    - Inherits from `IPropertyOwner` and `IFinancialAgent`.
    - Explicitly requires `current_wage` property (for mortgage calculations).
- **Hardened Agents**:
    - **Household**: Explicitly implemented `IPropertyOwner` (added `owned_properties`, `add_property`, `remove_property`) and `IHousingTransactionParticipant` (added `current_wage` property exposing `_econ_state`).
    - **Firm**: Explicitly implemented `IPropertyOwner` by adding `owned_properties` to `FinanceState` and exposing delegation methods.
- **Refactored Handler**:
    - Replaced `hasattr` checks with `isinstance(buyer, IHousingTransactionParticipant)` and `isinstance(seller, IPropertyOwner)`.
    - Removed legacy fallbacks, enforcing strict type compliance.
    - Simplified `_create_borrower_profile` and `_apply_housing_effects` to rely on trusted interfaces.

## 4. Lessons Learned & Technical Debt Identified
- **Protocol Composition**: Combining existing protocols (`IPropertyOwner`, `IFinancialAgent`) into a context-specific protocol (`IHousingTransactionParticipant`) is a powerful way to enforce requirements without creating "God Interfaces".
- **Agent State Exposure**: Agents often hide state in internal DTOs (`_econ_state`). Exposing these via properties to satisfy Protocols requires careful thought to maintain encapsulation while allowing necessary access.
- **Technical Debt**:
    - `IMortgageBorrower` in `modules/common/interfaces.py` defines `assets` as a `Dict`, while agents often implement `assets` as a `float` (Total Wealth). This mismatch forced us to use `IFinancialAgent` for balance checks instead of `IMortgageBorrower`. Future refactoring should align `IMortgageBorrower` with `IFinancialAgent`.
    - `Firm` currently implements `IPropertyOwner` but lacks logic to actually *use* real estate (e.g., for production or office space). It just holds it as an asset. Future work should integrate property ownership into `Firm`'s production/utility functions.
