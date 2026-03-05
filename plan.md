1. **Understand the Goal**: The objective is to decouple the `EconomicIndicatorTracker` from the internal state of agents (`Household`, `Firm`) and markets. We need to implement a "DTO Purity" pattern by introducing an `EconomyAnalyticsSnapshotDTO` and updating `EconomicIndicatorTracker.track()` to accept this DTO instead of raw agent lists.

2. **Create the DTOs**: We need to ensure that `EconomyAnalyticsSnapshotDTO` and related DTOs (`HouseholdAnalyticsDTO`, `FirmAnalyticsDTO`, `MarketAnalyticsDTO`) are fully implemented in `modules/analytics/api.py`. (I have already created this file based on the spec).

3. **Update `EconomicIndicatorTracker`**:
   - Change the signature of `track()` to `track_tick(self, snapshot: EconomyAnalyticsSnapshotDTO) -> None`.
   - Update the internal logic of `track_tick()` to compute metrics using the properties of the DTOs, completely removing any reliance on `_bio_state`, `_econ_state`, etc.
   - Address exception handling: handle missing data or zeros properly.

4. **Update the Orchestrator/WorldState (Snapshot Generation)**:
   - In `simulation/orchestration/phases/metrics.py` (specifically `Phase6_PostTickMetrics`), we need to build the `EconomyAnalyticsSnapshotDTO` from the simulation state before passing it to the tracker.
   - Implement the snapshot building logic, converting real agents into DTOs.

5. **Fix Broken Tests**:
   - `tests/test_economic_tracker_precision.py`
   - `tests/unit/test_metrics_hardening.py`
   - `tests/integration/scenarios/diagnosis/test_indicator_pipeline.py`
   - `tests/integration/test_reporting_pennies.py`
   - `tests/integration/test_wo058_production.py`
   - Any other tests calling `tracker.track()`. I will search for these calls and refactor them to use the new DTO and `track_tick()` method. Note that some tests might mock `tracker.track` and will need to assert that `track_tick` is called instead.

6. **Create Insight Report**:
   - Create `communications/insights/WO-IMPL-DTO-ANALYTICS.md` using the exact format requested.
   - Run the full test suite (`pytest`) and capture the output for the report.

7. **Pre-commit Steps**: Call `pre_commit_instructions` and follow them to ensure tests pass, logging is clean, and verification rules are met.
