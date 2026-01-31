# -C: Tech Adoption Barriers Analysis

**Objective**: Verify why `TECH_AGRI_CHEM_01` is not being adopted despite being unlocked.

**Hypothesis**: 
The `diffusion_rate` is too low, or the `human_capital_index` (HCI) is below 1.0, or firm sectors are not correctly matching the "FOOD" sector requirement in `TechnologyManager`.

**Tasks**:
1. **Audit**: Check `simulation/systems/technology_manager.py` diffusion logic.
2. **Analysis**: Check `config.py` for `TECH_ADOPTION_SENSITIVITY` and `TECH_DIFFUSION_RATE` values.
3. **Experimental Run**: Run 10 ticks and log the `HCI` and diffusion rolls for each firm.
4. **Report**: Identify the bottleneck (Math, HCI, or Sector Mismatch).
