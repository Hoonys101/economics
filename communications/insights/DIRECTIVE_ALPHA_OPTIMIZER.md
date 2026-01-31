# Insight Report: Directive Alpha Optimizer

## 1. Phenomenon
- **I/O Bottleneck**: The simulation was flushing logs to the database at every tick (`self.simulation_logger.flush()` in `simulation/engine.py`), causing significant overhead.
- **Consumption Logic**: The household consumption logic has been vectorized (`VectorizedHouseholdPlanner`) and integrated into `CommerceSystem`, effectively bypassing the legacy `Household.decide_and_consume` method for the decision-making part.

## 2. Cause
- **I/O**: Missing conditional check for `batch_save_interval` in the main simulation loop (`engine.py`).
- **Optimization**: Previous optimization efforts introduced `CommerceSystem` and `vectorized_planner.py` to handle scale, but the I/O bottleneck remained in the facade.

## 3. Solution
- **I/O Fix**: Hardcode `batch_save_interval = 50` in `simulation/engine.py` and condition the `flush()` call.
- **Vectorization**: Confirmed `simulation/ai/vectorized_planner.py` implements the required NumPy boolean mask logic and is utilized by `CommerceSystem`.

## 4. Technical Debt
- `Household.decide_and_consume` is now largely redundant for active decision making but remains in the codebase.
- The directive referenced `simulation/engine.py` line ~545 for a loop that now exists in `CommerceSystem` / `phases.py`, indicating documentation drift.
