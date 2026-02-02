# Spec: Workstream A - Core Agent & Manager Shims

## Objective
Restore essential properties and setters in `Household` to ensure backward compatibility and fix defensive logic in `FiscalPolicyManager`.

## Scope
1.  **simulation/core_agents.py**:
    *   Implement Getter/Setter bridges for: `assets`, `inventory`, `needs`, `is_active`, `is_homeless`, `is_employed`, `current_wage`, `residing_property_id`, `owned_properties`.
    *   Ensure `_add_assets` and `_sub_assets` correctly sync both `self._econ_state.assets` and `self._assets`.
2.  **modules/government/components/fiscal_policy_manager.py**:
    *   Fix `determine_fiscal_stance` to handle Mocked market data objects (ensure float conversion).

## Validation
- `python scripts/trace_leak.py` must run without any AttributeError.
