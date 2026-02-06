# SPEC: Watchtower HUD & Observability (Track 1)

## 1. Objective

Finalize the real-time observability layer by enhancing the data aggregation logic to use moving averages for key stability metrics and implementing the missing demographic metrics as per the original work order. This revision addresses architectural risks identified during pre-flight audit.

## 2. Architectural Solution & Implementation Plan

This plan supersedes the original draft, incorporating architectural constraints to maintain Separation of Concerns (SoC) and system stability.

### 2.1. Time-Series Metrics (SMA & Growth)

**Problem**: Directly implementing stateful moving average calculations in `DashboardService` violates SRP and makes it a God Class.

**Solution**: The `simulation.diagnostics.tracker.py` module will be enhanced to handle all time-series calculations. `DashboardService` will remain stateless, consuming the final values from the `Tracker`.

#### 2.1.1. `simulation.diagnostics.tracker.py` Modifications

-   **Add New State**: The `Tracker` class will be initialized with new instance attributes:
    ```python
    # In Tracker.__init__
    self.gdp_history = deque(maxlen=50)
    self.cpi_history = deque(maxlen=50)
    self.m2_leak_history = deque(maxlen=50)

    self.sma_gdp: float = 0.0
    self.sma_cpi: float = 1.0
    self.sma_m2_leak: float = 0.0
    self.gdp_growth: float = 0.0
    ```

-   **Update Logic**: The `Tracker.track_indicators` (or equivalent update method) will be modified.
    -   **Pseudo-code**:
    ```python
    # At the end of the tracking cycle for a tick
    # Previous GDP is needed for growth calculation
    previous_gdp = self.gdp_history[-1] if self.gdp_history else current_gdp

    self.gdp_history.append(current_gdp)
    self.cpi_history.append(current_cpi)
    self.m2_leak_history.append(current_m2_leak) # m2_leak must be calculated first

    # Update SMAs
    self.sma_gdp = sum(self.gdp_history) / len(self.gdp_history)
    self.sma_cpi = sum(self.cpi_history) / len(self.cpi_history)
    self.sma_m2_leak = sum(self.m2_leak_history) / len(self.m2_leak_history)

    # Update Growth Rate
    if previous_gdp > 0:
        self.gdp_growth = (current_gdp - previous_gdp) / previous_gdp
    else:
        self.gdp_growth = 0.0
    ```

#### 2.1.2. `simulation.orchestration.dashboard_service.py` Refactoring

-   **Modify `get_snapshot`**:
    -   The `m2_leak` calculation will be removed.
    -   The values for `gdp`, `cpi`, `m2_leak`, and a new `gdp_growth` field will be read directly from the `Tracker`.
    -   **Pseudo-code**:
    ```python
    # In DashboardService.get_snapshot()

    tracker = self.simulation.world_state.tracker

    # --- 1. System Integrity ---
    # OLD: m2_leak = self._calculate_m2_leak(state)
    # NEW:
    m2_leak = tracker.sma_m2_leak

    # ... FPS Calculation ...

    # --- 2. Macro Economy ---
    # OLD: gdp = latest.get("gdp", 0.0)
    # NEW:
    gdp = tracker.sma_gdp # Use the smoothed value for display
    cpi = tracker.sma_cpi # Use the smoothed value for display
    gdp_growth = tracker.gdp_growth

    # ...

    # Update DTO population
    snapshot = WatchtowerSnapshotDTO(
        # ...
        integrity=IntegrityDTO(m2_leak=m2_leak, fps=fps),
        macro=MacroDTO(
            gdp=gdp,
            cpi=cpi,
            unemploy=unemploy,
            gini=gini,
            gdp_growth=gdp_growth # Populate new field
        ),
        # ...
    )
    ```

### 2.2. Demographic Metrics (Birth Rate)

**Problem**: Implementing birth rate calculation inside `DashboardService` is inconsistent with the existing pattern for death rate calculation and breaks SoC.

**Solution**: Birth rate tracking will be implemented in the `simulation.state.repository` layer, following the established pattern for `death_rate`.

#### 2.2.1. `simulation.state.repository.py` (or similar data access layer)

-   **Task**: A mechanism to log birth events must be created, likely triggered by a `LifecycleManager`. The repository must be able to query these events.
-   **API**: A new method will be added to the `AgentRepository`.
    ```python
    # In AgentRepository
    def get_birth_counts(self, start_tick: int, end_tick: int, run_id: str) -> Dict[str, int]:
        """Counts the number of birth events within a given tick range."""
        # Implementation depends on how birth events are logged (e.g., SQL query, log parsing)
        # ...
        return {"birth_count": ...}
    ```

#### 2.2.2. `simulation.orchestration.dashboard_service.py` Refactoring

-   **Modify `get_snapshot`**: The `TODO` for birth rate will be replaced with a call to the new repository method.
    -   **Pseudo-code**:
    ```python
    # In DashboardService.get_snapshot() -> Population section

    repo = getattr(state, "repository", None)
    if repo and active_count > 0:
        start_tick = max(0, state.time - 5) # Use a consistent window

        # Death Rate (existing)
        attrition = repo.agents.get_attrition_counts(start_tick, state.time, run_id=state.run_id)
        death_count = attrition.get("death_count", 0)
        death_rate = (death_count / active_count) * 100.0

        # Birth Rate (NEW)
        # OLD: TODO: Implement Birth Rate tracking...
        # NEW:
        births = repo.agents.get_birth_counts(start_tick, state.time, run_id=state.run_id)
        birth_count = births.get("birth_count", 0)
        birth_rate = (birth_count / active_count) * 100.0

    # ... update PopulationMetricsDTO with both birth_rate and death_rate
    ```

## 3. DTO Modifications

### `simulation.dtos.watchtower.MacroDTO`

A new field must be added.

```python
class MacroDTO(TypedDict):
    gdp: float
    cpi: float
    unemploy: float
    gini: float
    gdp_growth: float # NEW: Percentage growth from previous tick
```

## 4. Verification & Testing

-   **Unit Tests**:
    -   `TestTracker`: Verify that `sma_gdp`, `sma_cpi`, `sma_m2_leak`, and `gdp_growth` are calculated correctly over a series of mock tick data.
    -   `TestAgentRepository`: Verify `get_birth_counts` correctly queries and aggregates mock birth events.
-   **Integration Tests**:
    -   `TestDashboardService`: Verify that the `get_snapshot` method correctly calls the `Tracker` and `Repository` mocks and populates the `WatchtowerSnapshotDTO` with the expected smoothed and demographic data.
-   **Golden Data & Mock Strategy**: No new golden data is required. Existing fixtures can be used. Mocks for `Tracker` and `Repository` will be essential for isolating `DashboardService` during testing.

## 5. Risk & Impact Audit

-   **`Tracker` Performance**: The `Tracker` is now stateful. The performance impact of appending to deques and recalculating sums every tick should be negligible for a 50-item window, but must be monitored.
-   **Dependency Inversion**: This design correctly places the responsibility for calculation in the `Tracker` and `Repository` modules, while the `DashboardService` acts as a pure assembler/aggregator. This adheres to the Dependency Inversion Principle.
-   **Refactoring Impact**: All consumers of `DashboardService` will now receive smoothed data for `gdp`, `cpi`, and `m2_leak`, and a new `gdp_growth` field. Frontend components must be updated to handle/display `gdp_growth`.

## 6. Mandatory Reporting

All insights gained during implementation, particularly regarding the performance of the `Tracker`'s new responsibilities, must be logged to a new file in `communications/insights/WO-XXX-Watchtower-Refinement.md`. This is a hard requirement for mission completion.

---

# SPEC: Operation Clean Sweep Refinement (Track 2)

## 1. Objective

Bridge the gap between individual firm R&D investment and global technology unlocks, while ensuring the technology diffusion system meets performance targets for 2,000+ agents. This revised specification addresses critical encapsulation and performance risks identified during pre-flight audit.

## 2. Architectural Solution & Implementation Plan

This plan supersedes the original draft, incorporating architectural constraints to ensure encapsulation, performance, and testability.

### 2.1. R&D Integration Bridge

**Problem**: The simulation orchestrator cannot access a firm's R&D investment for a given tick without breaking encapsulation by reaching into `firm.production.current_rd_investment`.

**Solution**: The `Firm` class will be modified to expose a clean, public API for retrieving the necessary information.

#### 2.1.1. `simulation.firms.py` Modification

-   **API**: A new public method `get_tech_info` will be added to the `Firm` class. This method is responsible for assembling the `FirmTechInfoDTO` from its internal state.

    ```python
    # In class Firm:
    from simulation.systems.tech.api import FirmTechInfoDTO # Ensure import

    def get_tech_info(self) -> FirmTechInfoDTO:
        """
        Gathers and returns the firm's technology-related information for the
        current tick, intended for use by the TechnologyManager.
        This serves as a clean public API, preventing encapsulation violation.
        """
        return FirmTechInfoDTO(
            id=self.id,
            sector=self.sector,
            # Delegate to the responsible internal component.
            current_rd_investment=self.production.current_rd_investment
        )
    ```

#### 2.1.2. Simulation Orchestrator (`simulation/engine.py` or similar) Refactoring

-   **Modify Main Loop**: The orchestrator's main tick loop will be updated to use this new public method.
    -   **Pseudo-code**:
    ```python
    # In Simulation.run_tick() or equivalent orchestrator method

    # ... after firms have made their decisions and R&D investment is determined ...

    # 1. Gather Tech Info via the public API
    firm_tech_infos: List[FirmTechInfoDTO] = [
        firm.get_tech_info() for firm in self.world_state.firms if firm.is_active
    ]

    # 2. Update TechnologyManager with the aggregated data
    self.world_state.technology_manager.update(
        current_tick=self.world_state.time,
        firms=firm_tech_infos,
        human_capital_index=self.world_state.tracker.get_latest_indicator("human_capital_index", 1.0)
    )
    ```

### 2.2. Performance & Benchmarking (`TechnologyManager`)

**Problem**: The `_process_diffusion` method contains a non-vectorized loop to build the `already_adopted_mask`, which will not scale and will fail the `<10ms` performance goal.

**Solution**: The core data structure for tracking technology adoption will be refactored from a `Dict[int, Set[str]]` to a structure that allows fully vectorized lookups.

#### 2.2.1. `simulation.systems.technology_manager.py` Refactoring

-   **Data Structure Change**:
    -   The `adoption_registry` will be changed. A mapping from `firm_id` to an integer index (`firm_id_to_idx`) will be maintained. The core data will be a 2D boolean `numpy` array.
    ```python
    # In TechnologyManager.__init__
    # New data structures
    self.firm_id_to_idx: Dict[int, int] = {}
    self.idx_to_firm_id: List[int] = []
    self.tech_id_to_idx: Dict[str, int] = {tech.id: i for i, tech in enumerate(self.tech_tree.values())}

    # The new adoption registry: a 2D numpy array [firm_idx, tech_idx]
    # This must be dynamically resizeable if firms can be added mid-simulation.
    # For a fixed number of firms, it can be initialized once.
    num_firms = ... # Get from config or initial state
    num_techs = len(self.tech_tree)
    self.adoption_matrix = np.zeros((num_firms, num_techs), dtype=bool)
    ```

-   **Refactor `_process_diffusion`**: The method will be rewritten for full vectorization.
    -   **Pseudo-code**:
    ```python
    # In TechnologyManager._process_diffusion

    # Assume firm_id_to_idx is populated and firm_data is aligned.
    firm_indices = np.array([self.firm_id_to_idx[f["id"]] for f in firms])
    sectors = np.array([f["sector"] for f in firms])

    for tech_id, tech_idx in self.tech_id_to_idx.items():
        tech = self.tech_tree[tech_id]
        if not tech.is_unlocked:
            continue

        effective_rate = self._get_effective_diffusion_rate(tech.diffusion_rate)

        # 1. Sector Mask (no change)
        sector_mask = (sectors == tech.sector) if tech.sector != "ALL" else np.ones(len(firms), dtype=bool)

        # 2. Adoption Mask (NEW: fully vectorized)
        # Select the column for the current tech and filter by the firms active this tick.
        already_adopted_mask = self.adoption_matrix[firm_indices, tech_idx]

        # 3. Candidates: In Sector AND Not Adopted (no change)
        candidate_mask = sector_mask & (~already_adopted_mask)
        candidate_indices_relative = np.where(candidate_mask)[0] # Indices relative to the 'firms' list

        if len(candidate_indices_relative) == 0:
            continue

        # 4. Roll Dice (no change)
        random_rolls = np.random.rand(len(candidate_indices_relative))
        newly_adopted_mask = random_rolls < effective_rate

        # 5. Determine Adopters
        adopter_indices_relative = candidate_indices_relative[newly_adopted_mask]

        # 6. Apply Adoption (NEW: vectorized update)
        # Get the absolute indices into adoption_matrix
        adopter_indices_absolute = firm_indices[adopter_indices_relative]
        self.adoption_matrix[adopter_indices_absolute, tech_idx] = True

        # Logging must be done carefully, perhaps in a loop over adopter_indices_absolute
        # or by batch-logging.
    ```

-   **Refactor `_adopt` and `has_adopted`**: These methods will now interface with the new `adoption_matrix`.

### 2.3. Market Integrity (Circuit Breakers)

**Status**: Correctly implemented in `OrderBookMarket`.

**Action**: No code changes required. The focus is on ensuring this critical feature is not broken. A new verification requirement is added.

## 3. Verification & Testing

-   **Unit Tests**:
    -   `TestFirm`: A new test to verify `firm.get_tech_info()` correctly retrieves and returns data from its components.
    -   `TestTechnologyManager`: Extensive tests are required for the refactored `_process_diffusion`. Test with various numbers of firms and techs to validate the vectorized logic against a simpler, loop-based implementation.
-   **Performance Benchmark**:
    -   The `scripts/bench_tech.py` script must be created as originally specified.
    -   It must initialize `TechnologyManager` with the refactored logic, populate it with 2,000+ mock firms, and run `_process_diffusion` over 1,000 ticks.
    -   The script must assert that the average execution time per tick is `< 10ms`.
-   **Integration Tests**:
    -   An integration test for `OrderBookMarket` must be created. This test will inject a series of volatile orders designed to trigger the circuit breakers and assert that out-of-bounds orders are rejected.

## 4. Risk & Impact Audit

-   **`TechnologyManager` Refactoring**: This is a high-risk, high-reward change. The logic for indexing and resizing the `adoption_matrix` must be flawless, especially if firms can enter/exit the simulation dynamically. The risk is mitigated by a dedicated performance benchmark and rigorous unit tests.
-   **Encapsulation**: The fix for the R&D bridge greatly improves system health by reinforcing encapsulation, reducing the risk of brittle, hidden dependencies.
-   **State Management**: The new `adoption_matrix` in `TechnologyManager` increases its memory footprint and state complexity. This state must be correctly handled during serialization/deserialization (saving/loading) of the simulation.

## 5. Mandatory Reporting

All insights gained during implementation, especially concerning the challenges of vectorization and the performance benchmarks of the new `TechnologyManager`, must be logged to a new file in `communications/insights/WO-XXX-Clean-Sweep-Refinement.md`. This is a hard requirement for mission completion.
