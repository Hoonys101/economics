# Command Execution Strategy (v2)

## Immediate Batch Execution Pattern
To prevent "Double Execution" where commands are processed by `Simulation` and then re-processed by `Phase0_Intercept`:

1.  **Drain & Batch**: `Simulation` drains the `god_command_queue` immediately at the start of a tick.
2.  **Atomic Execution**: Commands are executed via `CommandService.execute_command_batch`.
3.  **No Re-enqueue**: Executed commands are **never** put back into the queue. `Phase0_Intercept` will find an empty queue.
4.  **Baseline Integrity**: The `m2_delta` returned from the batch execution is immediately applied to `world_state.baseline_money_supply` to ensure zero-sum consistency.
