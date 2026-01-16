I have drafted the work order as requested. It is located at `design/work_orders/WO-079_Config_Automation.md`.

This work order explicitly addresses the architectural conflict found in the audit by mandating Dependency Injection and forbidding a global singleton for the `SimulationConfig`. It provides a clear, step-by-step plan for Jules, including the creation of the config schema, JSON profile files, modifications to the `SimulationInitializer`, and the refactoring of core modules.

The verification plan includes both a new unit test for the config loading mechanism and a critical regression test using the existing `test_engine.py` suite to ensure no behavioral changes are introduced. All constraints from the audit have been integrated as mandatory rules.
