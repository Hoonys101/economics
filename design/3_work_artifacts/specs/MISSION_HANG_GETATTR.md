# Hang Audit Hypothesis 2: Recursion in Simulation.__getattr__

## Objective
Determine if the hang is caused by an infinite loop or heavy blocking call within the `Simulation.__getattr__` delegation pattern.

## Context
The traceback always lands inside `Simulation.__getattr__`. `sim.bank.id` is called inside `_init_phase4_population`. If `bank` is missing, `__getattr__` delegates to `world_state`.

## Instructions
1. Audit `simulation/engine.py` specifically the `__getattr__` method.
2. Audit `simulation/world_state.py` for how `.bank` is retrieved. Is it a complex property?
3. Check `simulation/initialization/initializer.py` to see exactly *when* `sim.bank` is assigned. 
4. If `sim.bank` is queried *before* it is fully initialized, does it cause an infinite fallback loop between `engine` and `world_state`?
5. Conclude whether a recursion loop is the cause and propose a fix (e.g., explicit property declarations or `hasattr` guards).
