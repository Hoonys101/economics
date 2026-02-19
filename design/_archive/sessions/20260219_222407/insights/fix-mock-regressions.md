# Fix Mock Attribute Regressions (Cockpit 2.0)

## [Architectural Insights]

### Mock Drift and Protocol Fidelity
The previous implementation of `tests/modules/governance/test_cockpit_flow.py` and `tests/modules/governance/test_system_command_processor.py` utilized `MagicMock()` without specifying a `spec`. This approach allows "Mock Drift", where tests rely on attributes that do not exist in the real class, and fails to enforce "Protocol Fidelity" because generic mocks do not satisfy `isinstance(mock, Protocol)` checks for `@runtime_checkable` protocols unless specific attributes are manually set.

### Solution Strategy
1.  **Spec-Based Mocking**: We are replacing generic `MagicMock()` with `MagicMock(spec=RealClass)` (e.g., `Government`, `CentralBankSystem`). This ensures that:
    *   The mock only exposes attributes that exist on the real class (preventing drift).
    *   The mock satisfies `isinstance(mock, Protocol)` checks if the real class implements the protocol (enforcing fidelity).
2.  **DTO Compliance**: We are also mocking `fiscal_policy` with `MagicMock(spec=FiscalPolicyDTO)` to ensure that nested data structures also adhere to the expected schema.

## [Test Evidence]

```
tests/modules/governance/test_cockpit_flow.py::test_cockpit_command_flow_tax_rate
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:74 CommandService received CockpitCommand: SET_TAX_RATE
INFO     simulation.engine:engine.py:163 System Commands Queued for Tick 1: 1
INFO     simulation.orchestration.phases.system_commands:system_commands.py:29 SYSTEM_COMMANDS_PHASE | Processing 1 commands.
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
INFO     modules.governance.processor:processor.py:66 SYSTEM_COMMAND | Corporate Tax Rate: 0.2 -> 0.35
PASSED                                                                   [ 14%]
tests/modules/governance/test_cockpit_flow.py::test_cockpit_command_flow_pause
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:74 CommandService received CockpitCommand: PAUSE
INFO     simulation.engine:engine.py:147 Simulation PAUSED by CommandService.
PASSED                                                                   [ 28%]
tests/modules/governance/test_system_command_processor.py::test_set_corporate_tax_rate
-------------------------------- live log call ---------------------------------
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
INFO     modules.governance.processor:processor.py:66 SYSTEM_COMMAND | Corporate Tax Rate: 0.2 -> 0.25
PASSED                                                                   [ 42%]
tests/modules/governance/test_system_command_processor.py::test_set_income_tax_rate
-------------------------------- live log call ---------------------------------
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
INFO     modules.governance.processor:processor.py:75 SYSTEM_COMMAND | Income Tax Rate: 0.1 -> 0.15
PASSED                                                                   [ 57%]
tests/modules/governance/test_system_command_processor.py::test_set_base_interest_rate
-------------------------------- live log call ---------------------------------
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_INTEREST_RATE
INFO     modules.governance.processor:processor.py:98 SYSTEM_COMMAND | CB Base Rate: 0.05 -> 0.03
PASSED                                                                   [ 71%]
tests/modules/governance/test_system_command_processor.py::test_missing_government
-------------------------------- live log call ---------------------------------
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
ERROR    modules.governance.processor:processor.py:48 SYSTEM_COMMAND | Government agent is None.
PASSED                                                                   [ 85%]
tests/modules/governance/test_system_command_processor.py::test_protocol_guardrails
-------------------------------- live log call ---------------------------------
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
ERROR    modules.governance.processor:processor.py:53 SYSTEM_COMMAND | Government agent <class 'tests.modules.governance.test_system_command_processor.test_protocol_guardrails.<locals>.NotGovernment'> does not satisfy IGovernment protocol.
PASSED                                                                   [100%]
```
