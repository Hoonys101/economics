# Hang Audit Hypothesis 4: Mock Resolution / Test Setup Leaks

## Objective
Determine if the hang only occurs in test environments (`operation_forensics.py` often runs via `pytest` or loads test subsets) due to the infinite-depth evaluation of `MagicMock` objects.

## Context
If `sim.bank` or `sim.settlement_system` is a `MagicMock`, calling `register_account` evaluates lazily. In tight loops (10,000 iterations), this causes drastic CPU spikes masquerading as a hang.

## Instructions
1. Audit `simulation/initialization/initializer.py` to see if `sim.settlement_system` or `sim.bank` could inadvertently be initialized as a mock.
2. Audit `tests/mocks/mock_settlement_system.py` if present in the context. Is it used during forensics?
3. Review how `operation_forensics.py` builds the simulation. Does it use `create_simulation` from `simulation_builder.py` or a custom test harness?
4. Conclude if `MagicMock` overhead explains the hang, and propose a strict mock-containment boundary.
