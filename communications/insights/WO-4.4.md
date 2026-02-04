# Mission WO-4.4 Insights: Policy Lockout Manager

## Overview
Implemented `PolicyLockoutManager` to handle the "Scapegoat Mechanic" where firing an advisor locks their associated policies for a set duration (20 ticks).

## Implementation Details
- **Component**: `PolicyLockoutManager` in `modules/government/components/policy_lockout_manager.py`.
- **Integration**: `Government` agent instantiates the manager and checks it during key actions.
- **Trigger**: `Government.fire_advisor(school)` triggers the lockout.
- **Enforcement**:
    - `provide_household_support` checks `KEYNESIAN_FISCAL`.
    - `provide_firm_bailout` checks `KEYNESIAN_FISCAL`.

## Insights & Technical Debt

### Insights
1. **Government "God Object" Risk**: The `Government` class is accumulating many responsibilities (Taxation, Welfare, Infra, Monetary, Politics). While specialized managers (`WelfareManager`, `InfrastructureManager`) help, the `Government` class itself acts as a heavy facade.
2. **Policy Tagging**: Currently, tags are checked explicitly in methods. A decorator-based approach or a `PolicyEnforcer` middleware might be cleaner for "Tag all government actions" in the future, especially if the number of tags grows.

### Technical Debt
1. **Hardcoded Mappings**: The mapping between `EconomicSchool` and `PolicyActionTag` is currently hardcoded within `Government.fire_advisor`.
    - *Risk*: Violation of Open/Closed Principle. Adding a new school requires modifying `Government.py`.
    - *Recommendation*: Move this mapping to `PolicyLockoutManager` or a dedicated config/enum map.
2. **Partial Enforcement**: Only `provide_household_support` and `provide_firm_bailout` are currently guarded. Other implicit Keynesian actions (if any exist in `FiscalPolicyManager` logic) might not be strictly locked out, although `FiscalPolicyManager` is where the "stance" is determined.
    - *Note*: `fire_advisor` is a political action, so blocking the *execution* of specific high-level actions is a reasonable approximation for now.
