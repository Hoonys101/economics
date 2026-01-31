# Work Order: -Analysis-Refinement

## 1. Objective
Enable deep analysis of the Phase 23 failure by refining the verification script to produce clean, data-driven logs, and then generating a hypothesis report based on that data.

## 2. Tasks

### Task 1: Refine Verification Script
**Target File**: `scripts/verify_phase23_harvest.py`

**Instructions**:
1. **Reduce Noise**: Suppress standard `INFO` logs from the engine during the run (set log level to `WARNING` for core components if possible, or use a context manager).
2. **Structural Data Export**: Modify the script to append a **CSV-formatted line** to `reports/phase23_metrics.csv` at every tick (or every 10 ticks).
 - **Columns Required**:
 - `Tick`
 - `Food_Price_Avg`
 - `Total_Food_Inventory` (Sum of all firms' inventory)
 - `Household_Avg_Assets`
 - `Population_Count`
 - `Tech_Adoption_Count` (Number of firms with `TECH_AGRI_CHEM_01`)
 - `Unsold_Food_Ratio` (Total Inventory / Total Production)
3. **Console Output**: Keep the final "VERDICT" output but make the tick-by-tick progress bar cleaner.

### Task 2: Execute & Analyze
**Action**:
1. Run the refined script: `python scripts/verify_phase23_harvest.py > reports/refined_log.txt`
2. specific focus on `reports/phase23_metrics.csv`.

**Deliverable**:
Create `design/gemini_output/WO-099-Hypothesis_Report.md` containing:
- **Trend Analysis**: Did food inventory grow? Did price drop in response?
- **Blocker Identification**: "Price stayed high despite inventory -> Sticky Price Logic?" OR "Inventory never grew -> Production Failure?"
- **Hypothesis**: Propose 3 detailed hypotheses on why the "Great Harvest" failed.

## 3. Success Criteria
- [ ] `scripts/verify_phase23_harvest.py` produces `reports/phase23_metrics.csv`.
- [ ] `-Hypothesis_Report.md` provides clear, data-backed reasons for failure.
