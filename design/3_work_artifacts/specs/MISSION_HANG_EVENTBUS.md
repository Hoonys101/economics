# Hang Audit Hypothesis 3: Synchronous EventBus Stall

## Objective
Determine if `AccountRegistry.register_account` or `AgentRegistry.register` is triggering a massive wave of synchronous events that stalls the main thread.

## Context
In `modules/system/registry.py` and `account_registry.py`, adding an item to a dictionary might trigger an `EventBus` or observer pattern notification. If 10,000 agents register sequentially, this yields 10,000 synchronous broadcasts.

## Instructions
1. Audit `modules/finance/registry/account_registry.py`. Are there any hidden observer updates here?
2. Audit `modules/system/registry.py` (`AgentRegistry`). Does the `register` method trigger any heavy down-stream `WorldState` updates?
3. Look for `@enforce_purity` decorators or telemetry hooks firing synchronously on every single agent registration.
4. Conclude if synchronous event stalls are the root cause and propose a fix (e.g., bulk registration or async event emitting).
