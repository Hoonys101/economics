# Audit Report: Asset Leak and DTO Purity

## Executive Summary

The asset leak of `320.00` is tied to an untracked event during new agent initialization, though the exact code is not in the provided files. The DTO Purity Gate audit reveals that while direct agent object access has been eliminated, both decision engines (`AIDrivenHouseholdDecisionEngine`, `CorporateManager`) violate the purity principle by depending on their own internal `config_module` instead of the `context.config` DTO. Additionally, the household engine appears to access a live market object.

## 1. Asset Leak Analysis (`leak_hunt_result.txt`)

- **Status**: ⚠️ Root Cause Hypothesized
- **Evidence**:
  - The report confirms a total money supply increase of `320.00` (`leak_hunt_result.txt:L8-L10`).
  - This leak coincides with the creation of three new agents: `H_26`, `H_27`, and `H_28` (`leak_hunt_result.txt:L44`).
- **Diagnosis**:
  - The leak is not caused by the logic within `AIDrivenHouseholdDecisionEngine` or `CorporateManager`, as they only generate action requests (`Orders`) and do not handle agent creation.
  - The value `320.00` does not appear as a hardcoded value in the audited decision-making code.
  - **Conclusion**: The leak most likely originates from the agent initialization or reproduction process. The initial assets allocated to new households are being "minted" (created) rather than transferred from a parent or bank, and this creation is not being registered as an `Authorized` change in the system's monetary audit. The precise location of this logic is not present in the provided files but would be found in the module responsible for population management or agent creation.

## 2. DTO Purity Gate Audit

The audit assesses compliance with the principles laid out in `design/specs/DTO_PURITY_GATE_SPEC.md`.

### 2.1. `AIDrivenHouseholdDecisionEngine`

- **Status**: ⚠️ Partially Implemented / Violations Found
- **Findings**:
  - **Violation 1 (Configuration Dependency)**: The engine receives a `context.config` DTO but almost exclusively uses `self.config_module` to retrieve configuration parameters (e.g., `self.config_module.DSR_CRITICAL_THRESHOLD` on `ai_driven_household_engine.py:L94`). This makes the engine stateful and violates the principle of operating on pure inputs.
  - **Violation 2 (Live Object Access)**: The real estate logic accesses `context.markets["housing"]` (`ai_driven_household_engine.py:L478-L480`) and iterates through its `sell_orders` attribute. The DTO Purity spec intends for all market data to flow through the `market_data` DTO to prevent side effects from live object interactions. This appears to be a direct violation.
  - **Compliant**: The engine correctly uses `context.state` to access the household's state DTO and does not reference `context.household`.

### 2.2. `CorporateManager`

- **Status**: ⚠️ Partially Implemented / Violations Found
- **Findings**:
  - **Violation 1 (Configuration Dependency)**: The manager exclusively uses `self.config_module` for all configuration values (e.g., `self.config_module.FIRM_SAFETY_MARGIN` on `corporate_manager.py:L218`). It does not use a `FirmConfigDTO` from the context, which is a core requirement of the DTO Purity Gate design.
  - **Compliant**: The manager correctly uses the `firm: FirmStateDTO` passed to its methods and does not access a live `firm` object from the context.
  - **Note (Specification Discrepancy)**: The code accesses `context.market_snapshot` (`corporate_manager.py:L123`), a field that is missing from the `DecisionContext` definition in `DTO_PURITY_GATE_SPEC.md`. This indicates the specification is out of sync with the implementation.

## Risk Assessment

- **Configuration Management**: The widespread use of `self.config_module` instead of the `context.config` DTO undermines the goal of creating stateless, portable decision engines. It couples the logic to its initialization environment, making testing harder and increasing the risk of inconsistent behavior if not configured identically everywhere.
- **Leaky Abstraction**: The access to `context.markets` in the household engine perpetuates the original problem the DTO Purity Gate was designed to solve, creating a risk of unforeseen state changes and complex debugging.

## Conclusion

The DTO Purity Gate is only partially enforced. While direct agent object passing has been fixed, a "leaky" implementation remains. To achieve full compliance, `AIDrivenHouseholdDecisionEngine` and `CorporateManager` must be refactored to source all configuration exclusively from `context.config` DTOs, and the household engine's reliance on `context.markets` must be replaced with data from `context.market_data`.
