# Technical Insight Report: Phase 9.2 Track A (Financial SSoT)

**Mission Key:** PH9.2_TrackA
**Status:** IMPLEMENTED
**Date:** 2026-02-10

## 1. Problem Phenomenon
The legacy `SettlementSystem` relied on direct attribute access (`agent.assets`) and untyped checks (e.g., `hasattr(agent, 'wallet')`) to perform financial transfers. This violated the Single Source of Truth (SSoT) principle and made it impossible to enforce zero-sum integrity, as any module could arbitrarily mutate an agent's cash balance. Furthermore, the `Bank` class had ambiguous interfaces for accessing its own equity versus customer deposits.

## 2. Root Cause Analysis
*   **Lack of Formal Protocols:** There was no strict contract defining what a "Financial Agent" is. Agents implemented ad-hoc methods or exposed raw state.
*   **Ambiguous Dependencies:** `SettlementSystem` depended on `Optional[Any]` for the bank, leading to "duck typing" that was fragile and hard to test.
*   **Method Name Collision:** Both the generic financial agent interface and the specific banking service interface used `get_balance`, but with different semantics (Own Equity vs. Customer Deposit).

## 3. Solution Implementation Details
### 3.1 Protocol Definition
We introduced two strict protocols in `modules/finance/api.py`:
1.  `IFinancialAgent`: Defines `deposit`, `withdraw`, and `get_balance(currency)`. This represents an entity's *own* wallet.
2.  `IBank`: Defines banking services. Crucially, we renamed the customer balance accessor to `get_customer_balance(agent_id)` to avoid conflict with `IFinancialAgent.get_balance`.

### 3.2 Refactoring
*   **SettlementSystem:** Refactored `transfer` and `_execute_withdrawal` to use `IFinancialAgent` methods exclusively. It now uses the EAFP (Easier to Ask for Forgiveness than Permission) pattern by attempting `withdraw` and catching `InsufficientFundsError`, rather than inspecting state beforehand.
*   **Agents:** Updated `Household`, `Firm`, `Government`, and `Bank` to strictly implement `IFinancialAgent`.
*   **Bank:** Implemented dual interfaces. The `Bank` acts as an `IFinancialAgent` for its reserves and an `IBank` for its customers.

## 4. Lessons Learned & Technical Debt
*   **Protocol Method Collisions:** When an entity plays multiple roles (e.g., Bank as an Agent and Bank as a Service), method names must be distinct. `get_balance` was too generic. We resolved this by renaming the service method to `get_customer_balance`.
*   **Dependency Injection:** Injecting `IBank` into `SettlementSystem` (instead of `Any`) allowed for robust type checking and clearer intent.
*   **Legacy Support:** We left some legacy fallbacks (e.g., checking `IFinancialEntity`) in `SettlementSystem` to prevent immediate regression in untested corners of the simulation, but these should be removed in a future cleanup phase.
*   **Technical Debt:** The `CurrencyCode` type alias is just `str`, which limits static analysis. Future refactoring should consider making it a NewType or Enum.
