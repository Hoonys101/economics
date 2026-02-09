# Structural Architecture Repair Report (STRUCTURAL-REPAIR-GO)

## 1. Problem Phenomenon
The simulation experienced multiple crashes and critical failures due to regressions introduced during recent refactoring efforts (likely Protocol Shield Hardening or similar).

**Symptoms:**
- `AttributeError: 'Household' object has no attribute 'generation'`
- `AttributeError: 'Firm' object has no attribute 'finance'`
- `AttributeError: 'Household' object has no attribute 'portfolio'`
- `AttributeError: 'Firm' object has no attribute 'revenue_this_turn'`
- `AttributeError: 'Firm' object has no attribute 'cost_this_turn'`
- `AttributeError: property 'current_wage' of 'Household' object has no setter`
- `AttributeError: 'Household' object has no attribute 'consume'`
- `AttributeError: 'Household' object has no attribute 'residing_property_id'`
- `SETTLEMENT_FATAL`: Welfare transfers failed because `debit_id` was `None`.

These errors indicated a systematic loss of API compatibility in Core Agents (`Household`, `Firm`) where properties and methods expected by various System Handlers (`FinancialTransactionHandler`, `TaxationSystem`, `CommerceSystem`, etc.) were removed or not exposed.

## 2. Root Cause Analysis
The root cause was an incomplete transition to the "Orchestrator-Engine" pattern and Strict DTO usage.

1.  **Missing Proxy Properties:** When state was moved to `_econ_state` and `_bio_state` DTOs, the corresponding property accessors on the Agent classes (`Household`, `Firm`) were not fully implemented or were removed, breaking backward compatibility with existing Systems that rely on direct attribute access (e.g., `agent.generation`, `firm.revenue_this_turn`).
2.  **Missing Legacy Components:** The `firm.finance` component was likely removed in favor of `FinanceEngine` (stateless), but legacy code still accessed `firm.finance.*`.
3.  **Missing Setters:** Some properties were exposed as read-only getters (delegating to DTOs) but lacked setters, causing failures when Systems tried to update agent state (e.g., `labor_handler` updating `current_wage`).
4.  **String vs Object Identity:** `WelfareManager` generated payment requests with `payer="GOVERNMENT"` (string), but the `Government` agent's execution logic expected the payer to be resolved to `self` only if it matched `self.id`, failing to handle the string literal, leading to `SettlementSystem` receiving a string instead of an agent object/ID.

## 3. Solution Implementation Details

### 3.1. Household Agent Restoration (`simulation/core_agents.py`)
Restored missing properties and methods to bridge the gap between Systems and Internal State DTOs:
- **Properties:** `generation`, `portfolio`, `residing_property_id`, `is_homeless`.
- **Setters:** Added setters for `current_wage`, `residing_property_id`, `is_homeless`.
- **Methods:** Re-implemented `consume(item_id, amount)` to handle inventory removal and state tracking, satisfying `CommerceSystem`.

### 3.2. Firm Agent Restoration (`simulation/firms.py`)
Restored legacy accessors to maintain compatibility:
- **Finance Proxy:** Added `@property def finance(self)` returning `self`. This allows calls like `firm.finance.record_expense()` to resolve to `firm.record_expense()` (which exists).
- **Financial State Exporters:** Added properties `revenue_this_turn`, `expenses_this_tick`, and `cost_this_turn` delegating to `self.finance_state`.

### 3.3. Engine Hardening
- **HREngine (`simulation/components/engines/hr_engine.py`):** Added safety checks for `labor_income_this_tick` to default to `0.0` if missing or `None`.
- **DemographicManager (`simulation/systems/demographic_manager.py`):** Added safety check for `parent.talent` inheritance, using a default `Talent` object if missing.

### 3.4. Government Welfare Fix (`simulation/agents/government.py`)
- Updated `execute_social_policy` to check if `req.payer == "GOVERNMENT"` (string). If so, it resolves `payer` to `self` (the Government agent instance), ensuring valid objects are passed to `SettlementSystem`.

## 4. Lessons Learned & Technical Debt
- **Interface Stability:** Refactoring core entities (Agents) requires strict adherence to existing interfaces (implicit or explicit) used by Systems. The "Orchestrator" pattern must fully wrap the internal DTOs.
- **Verification Gaps:** The unit tests might be mocking Agents with `MagicMock` which accepts any attribute access, hiding the missing properties on the actual classes. Integration tests (`trace_leak.py`) are crucial for catching these.
- **Stringly Typed IDs:** The mix of Integer IDs and String IDs (e.g. "GOVERNMENT") in transaction flows creates fragility. A strict type system for Agent IDs is recommended (Technical Debt).
- **Legacy Proxies:** The `firm.finance` returning `self` is a temporary hack. Future refactoring should update all consumers to use `firm` directly and remove the proxy.
