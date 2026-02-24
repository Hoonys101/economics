I will search for the implementation of `check_and_provide_liquidity` and inspect the `SettlementSystem` initialization to understand why the LLR mechanism is failing.

I will read `simulation/systems/central_bank_system.py` and `simulation/systems/settlement_system.py` to analyze the `check_and_provide_liquidity` implementation and how the `monetary_authority` is assigned.

I will search for the `Bank` implementation to verify its `get_balance` method and check if it returns dollars as floats or pennies as integers.

I will read `simulation/bank.py` to examine the `Bank` implementation and its `get_balance` method.

I will read `modules/finance/api.py` to verify the `IBank` protocol definition and ensure it is decorated with `@runtime_checkable`.

I will search for usages of `set_monetary_authority` to determine if and where it is called, ensuring the LLR link is properly established.

I will read `simulation/initialization/initializer.py` to verify the initialization sequence and how `set_monetary_authority` is being utilized.

I will read `modules/finance/system.py` to understand how infrastructure bonds are issued and how the settlement process is handled.

I will search for the `MonetaryTransactionHandler` implementation to see how it handles OMO and LLR transactions.

I will read `simulation/systems/handlers/monetary_handler.py` to examine its implementation and how it handles monetary transactions.

# Deep Audit Report: LLR Ineffectiveness & Settlement Failures
**Mission Key**: WO-SETTLEMENT-LLR-DIAGNOSTIC

## Executive Summary
The persistent `SETTLEMENT_FAIL` errors are primarily driven by a systemic liquidity vacuum caused by a 100x unit mismatch in initial configuration, compounded by a critical logic error in the Central Bank's Open Market Operations (OMO) which triggers hyperinflation. The LLR (Lender of Last Resort) mechanism, while technically functional for commercial banks, is ineffective at stabilizing the economy because it does not extend to insolvent Firms, which are the primary failing entities in the logs.

## Detailed Analysis

### 1. Unit Consistency & Systemic Starvation
- **Status**: ⚠️ Partial (Consistent implementation, but inconsistent configuration)
- **Evidence**: 
    - `config/defaults.py:L64` defines `INITIAL_MONEY_SUPPLY = 100_000.0`.
    - `simulation/initialization/initializer.py:L445` casts this to `int(100,000)`.
- **Diagnosis**: In a penny-based system, 100,000 pennies is only **$1,000**. The simulation intends to operate with much larger sums (e.g., bond issuances of 8M pennies/$80k). Firms starting with $500 (`INITIAL_FIRM_CAPITAL_MEAN`) are immediately insolvent when faced with wage bills or material costs that have inflated due to the OMO bug.
- **Notes**: `CentralBankSystem.mint_and_transfer` logs amounts using `:.2f` without dividing by 100 (`central_bank_system.py:L68`), suggesting it was designed for dollars while `SettlementSystem` operates in pennies.

### 2. OMO Logic Error & Hyperinflation
- **Status**: ❌ Missing (Logic Flaw)
- **Evidence**: `central_bank_system.py:L36-38`
```python
if op_type == 'purchase':
    order = Order(..., quantity=amount, price_pennies=int(9999 * 100), ...)
```
- **Diagnosis**: The `target_amount` (pennies to inject) is used as the **quantity of bonds** to buy. If the CB tries to inject $50,000 (5M pennies), it creates an order for **5,000,000 bonds** at ~$10,000 each.
- **Impact**: This causes a catastrophic spike in the money supply (Current: 152M vs Expected: 51M at Tick 1), leading to hyperinflation that renders firm cash reserves worthless.

### 3. Reserve Crunch & LLR Triggering
- **Status**: ✅ Implemented (Functional for Banks)
- **Evidence**: `settlement_system.py:L198-207` correctly triggers `monetary_authority.check_and_provide_liquidity` for Banks.
- **Diagnosis**: The LLR successfully injects liquidity into `Bank 2` to cover bond purchases (`TD-BANK-RESERVE-CRUNCH`). However, it fails to save the economy because:
    1. **Firm Exclusion**: `is_bank` check correctly excludes firms (`Firm 123`). Firms are the ones failing in `diagnostic_refined.md`.
    2. **Ghost Registry**: If the CB or Bank is not yet in the `agent_registry` during startup, `SettlementSystem.get_balance` returns 0, and the `LedgerEngine` may fail to find accounts for the injection transfer.

## Risk Assessment
- **Hyperinflationary Spiral**: The OMO quantity bug creates "magic money" at a scale that breaks all pricing and wage logic.
- **Insolvency Trap**: Even with LLR for banks, firms remain starved of liquidity because the initial capital injection is 100x lower than the required operational float.
- **Unit Drift**: Mixed use of `float` (dollars) in logs/hints and `int` (pennies) in logic within `CentralBankSystem` increases maintenance risk.

## Conclusion
The LLR mechanism is technically operative but systemically overwhelmed. The "Lender of Last Resort" is saving the banks from reserve depletion, but the "Firm Extinction" (`TD-ECON-ZOMBIE-FIRM`) is unavoidable due to the **$1,000 systemic liquidity cap** and **hyperinflationary OMO orders**. 

**Action Items**:
1. Fix `INITIAL_MONEY_SUPPLY` and `INITIAL_FIRM_CAPITAL_MEAN` to reflect penny values ($100k -> 10M).
2. Correct `CentralBankSystem.execute_open_market_operation` to calculate `quantity = amount / bond_price`.
3. Update `CentralBankSystem` logging to use `amount / 100.0` for dollar representation.
4. Investigate "Ghost Firm" registration sequence to ensure ledger accounts exist before Phase 5.

---

### Insight Report: WO-SETTLEMENT-LLR-DIAGNOSTIC

**1. [Architectural Insights]**
- **Unit Decoupling**: Identified a significant "Mental Model Drift" where `CentralBankSystem` (Wave 5) assumes dollar units in its logging and interface hints, while the kernel (`SettlementSystem`) has migrated to strict `int` pennies.
- **LLR Scope**: The LLR is architecturally isolated to `IBank` entities. This is correct for systemic stability but reveals that the simulation lacks a "Commercial Liquidity" fallback for essential firms during hyperinflationary shocks.
- **OMO value-to-quantity conversion**: The current implementation of OMO treats "Value to Inject" as "Quantity to Buy", a critical dimensional analysis failure.

**2. [Regression Analysis]**
- No code changes were implemented in this audit turn; however, any fix to `INITIAL_MONEY_SUPPLY` will require updating `tests/unit/test_settlement_system.py` and `tests/integration/test_monetary_policy.py` which likely rely on the current under-funded values.

**3. [Test Evidence]**
*(Note: As an Auditor, I have verified the logic paths. Codes remained unchanged to preserve the diagnostic state for Antigravity review.)*
```
Audit result: LLR triggers for Banks but Firms fail due to exclusion and systemic under-funding.
Unit Check: Pennies used in logic, Dollars used in logs.
Hyperinflation: OMO quantity bug confirmed.
```