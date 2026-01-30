# Audit Report: `demographic_manager.py` - Inheritance Zero-Sum Compliance

## Executive Summary
The `handle_inheritance` function in `demographic_manager.py` contains a critical zero-sum violation due to floating-point arithmetic, where asset distribution among heirs can result in lost fractions of currency. The implementation also inconsistently bypasses the project's `SettlementSystem`, which is correctly used for transfers in other parts of the same file, thereby missing opportunities for atomic transactions and centralized logging.

## Detailed Analysis

### 1. Does `deceased._sub_assets` match `sum(heir._add_assets)` EXACTLY?
- **Status**: ❌ Missing
- **Evidence**: `simulation/systems/demographic_manager.py:L315-L317`
- **Notes**: While the formula `net_amount = amount - tax` and `share = net_amount / len(heirs)` is logically correct, the division is performed using floating-point numbers. The sum of `share` distributed to all heirs does not guarantee to be exactly equal to `net_amount` due to potential rounding inaccuracies. The final call to `deceased_agent._sub_assets(deceased_agent.assets)` subtracts the original total, but the sum of parts (heir shares + tax) may not equal this total, causing a leak.

### 2. Are leftovers/roundings handled or lost?
- **Status**: ❌ Missing
- **Evidence**: `simulation/systems/demographic_manager.py:L315`
- **Notes**: The code does not have a mechanism to handle rounding residuals. For example, if `$99.99` is split among 3 heirs, each receives `$33.33`, and `$0.02` evaporates without being accounted for or distributed. There is no logic to assign the remainder to the state or the first heir.

### 3. Should this be refactored to use `SettlementSystem.transfer`?
- **Status**: ⚠️ Partial
- **Evidence**: `simulation/systems/demographic_manager.py:L316`, `simulation/systems/demographic_manager.py:L323`
- **Notes**: The function directly manipulates agent assets via `_add_assets` and `_sub_assets`. This is inconsistent with the `process_births` function within the same file, which correctly uses `settlement.transfer(parent, child, initial_gift, "BIRTH_GIFT")` (`L226-L231`). Refactoring `handle_inheritance` to use `SettlementSystem.transfer` for both the heir distributions and the tax payment would improve atomicity, centralize transaction logging, and provide a single place to enforce zero-sum rules.

### 4. Identify any logic where money might 'evaporate' during agent death.
- **Status**: ✅ Implemented (Found)
- **Evidence**: `simulation/systems/demographic_manager.py:L315`
- **Notes**: The primary point of money evaporation is the unhandled rounding residuals from floating-point division when calculating each heir's `share`. Additionally, the comment `// No heirs -> State (Tax) // return # Already handled by existing liquidation logic...` (`L299-L300`) points to a dependency on an external system. If that external logic fails or is misconfigured, the assets of heirless agents could be lost, although this function itself does not cause that particular evaporation.

## Risk Assessment
- **High Risk**: The current implementation guarantees small but consistent money leakage from the economy over time, violating the zero-sum principle.
- **Medium Risk**: The inconsistent use of direct asset manipulation versus the `SettlementSystem` introduces technical debt, complicates auditing, and increases the risk of transactional errors.

## Conclusion
The `handle_inheritance` method is not zero-sum compliant and must be refactored. The division logic needs to be replaced with a robust distribution algorithm that accounts for remainders, and all asset movements should be executed via the `SettlementSystem` to ensure transactional integrity and align with project conventions.
