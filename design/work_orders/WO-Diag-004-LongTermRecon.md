# WO-Diag-004: Long-Term Recon (Normal Conditions)

## 1. Background
Now that the "Immortality Bug" (missing `update_needs`) is fixed and the death mechanism has been verified via the Malthusian Stress Test, we need to return to the original problem: why are agents dying in a "normal" 1000-tick simulation?

## 2. Objective
Run a 1000-tick simulation under standard economic parameters to capture and classify agent deaths. This will reveal if the starvation is due to job shortages (Type A), labor apathy (Type B), or consumption glitches (Type C).

## 3. Scope of Work
*   **Execution**: Run the newly created script `scripts/recon_normal_1000.py`.
*   **Analysis**: Review the generated `reports/RECON_REPORT.md`.
*   **Reporting**: Summarize the death classification results and identify the "real" cause of starvation.

## 4. Parameters (Automatic in script)
*   **Duration**: 1000 Ticks
*   **Initial Assets**: 5000.0 (Normal)
*   **Stimulus**: Enabled (True)
*   **Consumption**: 1.0 per tick (Normal)

## 5. Success Criteria
*   Successfully completion of 1000 ticks.
*   Generation of `reports/RECON_REPORT.md` with accurate classification data.
