# Mission: Finance Parameter Migration (TD-034, TD-041)

## Context
We are moving away from hardcoded economic constants to a fully configurable simulation. Your task is to extract hidden financial parameters into the `config/` system.

## Task Details

### 1. Hardcoded Debt Parameters (TD-034)
- **Problem**: Bond maturity lengths, risk premia, and debt ceilings are hardcoded in `simulation/agents/government.py` or finance modules.
- **Action**: 
    - Identify these constants.
    - Add them to the global config (e.g., `config/economy_params.yaml`).
    - Update the code to read these via `ConfigManager`.

### 2. Bailout Covenant Ratio (TD-041)
- **Problem**: The repayment ratio of 0.5 for corporate bailouts is hardcoded.
- **Action**: 
    - Move `BAILOUT_COVENANT_RATIO` to the configuration system.
    - Default remains `0.5`, but it must be adjustable without code changes.

## Verification Requirements
- The simulation must run (`python main.py --ticks 10`) without any change in behavior using default config values.
- Verify that changing these values in the config file actually affects the simulation (e.g., shorter bond maturity).

## Success Criteria
- ✅ No hardcoded debt constants in logic files.
- ✅ Corporate bailout terms are fully configurable.
