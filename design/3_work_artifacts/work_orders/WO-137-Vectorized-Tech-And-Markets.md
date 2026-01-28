# Work Order: WO-137 - Vectorized Technology Diffusion

**Phase:** 23 (Performance)
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement
The current `TechnologyManager` implementation uses nested loops to process technology diffusion, iterating through each active technology and then each firm. This results in `O(T * F)` complexity, which does not scale to simulations with thousands of agents, causing significant performance bottlenecks. The agent-centric object model and Python-native data structures (`dict` of `sets`) are incompatible with high-performance vectorized computation.

## 2. Objective
Refactor the technology diffusion logic using NumPy to achieve sub-second performance for simulations involving at least 2,000 agents. This involves extracting the core computational logic into a new, vectorized "System" that operates on flat data arrays, while preserving the existing agent-based architecture.

## 3. Proposed Architecture: The "System" Pattern

To avoid a disruptive rewrite of the `Firm` agent, we will introduce a dedicated, stateless `TechnologySystem` class responsible for all vectorized computations. The existing `TechnologyManager` will be refactored to act as a controller, orchestrating the data flow between the agent object world and the vectorized system.

The workflow will follow a strict **Sync → Process → Commit** cycle each tick:

1.  **Sync**: The `TechnologyManager` will extract the necessary data (ID, sector, visionary status) from the list of all `Firm` objects into structured NumPy arrays. This is done once per tick.
2.  **Process**: The `TechnologyManager` will pass these NumPy arrays to the `TechnologySystem`, which performs all diffusion calculations (unlocks, adoption checks, random trials) in a purely functional, vectorized manner. The system returns a new, updated `adoption_matrix`.
3.  **Commit**: The `TechnologyManager` receives the updated `adoption_matrix` and stores it internally. The `get_productivity_multiplier` method will now use this matrix for lookups instead of the old dictionary-based registry.

This hybrid approach isolates the high-performance code and minimizes changes to the core agent models, mitigating the risks identified in the pre-flight audit.

## 4. Data Model: NumPy Schema

The `TechnologySystem` will operate exclusively on the following NumPy arrays. `TechnologyManager` will be responsible for creating and managing these data structures and their corresponding index mappings.

-   **Mappings (Managed by `TechnologyManager`)**:
    -   `firm_id_to_idx: Dict[int, int]`
    -   `tech_id_to_idx: Dict[str, int]`

-   **Core Data Arrays (Managed by `TechnologySystem`)**:
    -   `firm_properties: np.ndarray`:
        -   Shape: `(num_firms, num_properties)`
        -   dtype: `int32`
        -   Columns: `[sector_id, is_visionary]` (e.g., `sector_id` is an integer mapping to "FOOD", "MANUFACTURING", etc.)
    -   `tech_properties: np.ndarray`:
        -   Shape: `(num_techs, num_properties)`
        -   dtype: `float32`
        -   Columns: `[sector_id, multiplier, unlock_tick, diffusion_rate, is_unlocked]`
    -   `adoption_matrix: np.ndarray`:
        -   Shape: `(num_firms, num_techs)`
        -   dtype: `bool`
        -   Value: `True` if `firm[i]` has adopted `tech[j]`. This replaces the `adoption_registry` dictionary.

## 5. Detailed Logic (Pseudo-code)

### `TechnologyManager` (Refactored Controller)

```python
class TechnologyManager:
    def __init__(self, config, logger, strategy):
        # ... existing init ...
        self.tech_system = TechnologySystem() # New vectorized system
        self._initialize_mappings_and_arrays()

    def _initialize_mappings_and_arrays(self):
        # 1. Build tech_id_to_idx map and tech_properties array from config/strategy
        # 2. firm_id_to_idx and firm_properties will be built on first update

    def update(self, current_tick: int, firms: List[FirmTechInfoDTO], human_capital_index: float):
        # --- 1. SYNC Phase ---
        # (Re)build firm mappings and properties array if firms have changed
        self._sync_firm_data(firms)

        # --- 2. PROCESS Phase ---
        # Delegate computation to the vectorized system
        new_adoption_matrix = self.tech_system.update(
            current_tick,
            self.adoption_matrix,
            self.firm_properties,
            self.tech_properties,
            human_capital_index
        )

        # --- 3. COMMIT Phase ---
        # Store the new state. The old state is implicitly discarded.
        self.adoption_matrix = new_adoption_matrix

    def get_productivity_multiplier(self, firm_id: int) -> float:
        # Use fast NumPy lookup
        firm_idx = self.firm_id_to_idx.get(firm_id)
        if firm_idx is None:
            return 1.0

        # Get boolean vector of adopted techs for this firm
        adopted_techs_mask = self.adoption_matrix[firm_idx, :]

        # Get multipliers for all techs, apply mask, and calculate product
        all_multipliers = self.tech_properties[:, 1] # Multiplier column
        firm_multipliers = all_multipliers[adopted_techs_mask]

        return np.prod(firm_multipliers, initial=1.0)

    def _sync_firm_data(self, firms: List[FirmTechInfoDTO]):
        # Logic to build `firm_id_to_idx` and `firm_properties` array
        # This should be optimized to run only when the firm list changes.
        pass
```

### `TechnologySystem` (New Vectorized Engine)

```python
class TechnologySystem:
    def update(self, current_tick, adoption_matrix, firm_props, tech_props, hci) -> np.ndarray:
        # --- Stage 1: Unlock New Tech ---
        was_unlocked = tech_props[:, 4].astype(bool)
        unlock_ticks = tech_props[:, 2]
        newly_unlocked_mask = ~was_unlocked & (unlock_ticks <= current_tick)

        if np.any(newly_unlocked_mask):
            # Update the 'is_unlocked' status in the properties array
            tech_props[newly_unlocked_mask, 4] = 1.0

            # --- Stage 2: Early Adoption by Visionaries ---
            # Visionary firms are where firm_props[:, 1] == 1
            visionary_mask = firm_props[:, 1].astype(bool)

            # Create a broadcast-compatible adoption update
            # Shape: (num_firms, num_techs)
            # True where a visionary firm meets a newly unlocked tech
            visionary_adoption_update = np.outer(visionary_mask, newly_unlocked_mask)

            # TODO: Add sector matching logic here using masks
            # For now, assume all techs are for all sectors

            # Apply the update to the main adoption matrix
            adoption_matrix = np.logical_or(adoption_matrix, visionary_adoption_update)

        # --- Stage 3: Process Diffusion (S-Curve) ---
        unlocked_techs_mask = tech_props[:, 4].astype(bool)
        if not np.any(unlocked_techs_mask):
            return adoption_matrix # No unlocked techs, nothing to do

        # Get properties of only unlocked techs
        unlocked_tech_indices = np.where(unlocked_techs_mask)[0]
        active_tech_diffusion_rates = tech_props[unlocked_techs_mask, 3]

        # Calculate effective rates for all active techs at once
        boost = min(1.5, 0.5 * max(0.0, hci - 1.0))
        effective_rates = active_tech_diffusion_rates * (1.0 + boost)

        # Find potential adopters: firms that have NOT adopted the active techs
        # Shape: (num_firms, num_active_techs)
        potential_adopters_mask = ~adoption_matrix[:, unlocked_tech_indices]

        # Generate random numbers for every potential adoption event at once
        # Shape: (num_firms, num_active_techs)
        random_trials = np.random.rand(adoption_matrix.shape[0], len(unlocked_tech_indices))

        # Determine new adoptions vectorially
        # Shape: (num_firms, num_active_techs)
        newly_adopted_mask = potential_adopters_mask & (random_trials < effective_rates)

        # Update the main adoption matrix for the corresponding active tech columns
        adoption_matrix[:, unlocked_tech_indices] = np.logical_or(
            adoption_matrix[:, unlocked_tech_indices],
            newly_adopted_mask
        )

        return adoption_matrix

### Track B: Dynamic Circuit Breaker Implementation

1.  **Modify `simulation/markets/core_markets.py`**:
    -   Replace the hardcoded `CIRCUIT_BREAKER_LIMIT = 0.15`.
    -   Add a `VolatilityTracker` or use existing market metrics to calculate 20-tick rolling volatility.
    -   Implement `get_dynamic_limit()`:
        ```python
        def get_dynamic_limit(self, current_volatility: float) -> float:
            base_limit = self.config.BASE_CIRCUIT_BREAKER_LIMIT # e.g., 0.10
            # Scale limit between 5% and 30% based on volatility
            return max(0.05, min(0.30, base_limit * (1.0 + current_volatility)))
        ```
    -   Update the order matching logic to use this dynamic limit.
```

## 6. API Definition (`modules/systems/tech/api.py`)

A new `api.py` will define the formal interface for the technology system.

```python
# modules/systems/tech/api.py

from typing import Protocol, List, Dict
import numpy as np

# This DTO is assumed to exist from the context
from simulation.systems.tech.api import FirmTechInfoDTO

class ITechnologySystem(Protocol):
    """
    Interface for a vectorized technology diffusion system.
    """
    def update(
        self,
        current_tick: int,
        adoption_matrix: np.ndarray,
        firm_properties: np.ndarray,
        tech_properties: np.ndarray,
        human_capital_index: float
    ) -> np.ndarray:
        """
        Processes one tick of technology diffusion and returns the new state.

        Args:
            current_tick: The current simulation tick.
            adoption_matrix: (F, T) bool array of current adoptions.
            firm_properties: (F, P_f) array of firm data.
            tech_properties: (T, P_t) array of tech data.
            human_capital_index: The simulation's current HCI.

        Returns:
            A new (F, T) bool array representing the updated adoption state.
        """
        ...

class IVolatilityMarket(Protocol):
    """
    Interface for markets support dynamic volatility-based limits.
    """
    def calculate_volatility(self) -> float:
        """Returns the current rolling volatility of price changes."""
        ...
    
    def update_circuit_breaker(self):
        """Adjusts the price limits based on current volatility."""
        ...
```

## 7. Verification Plan

1.  **Unit Tests for `TechnologySystem`**:
    -   Create a new test file `tests/systems/test_technology_system.py`.
    -   Test `update` with fixed NumPy inputs and predictable `np.random.seed`.
    -   Verify that new technologies are unlocked at the correct tick.
    -   Verify that visionary firms adopt new tech immediately.
    -   Verify that the diffusion logic correctly updates the `adoption_matrix`.
    -   Verify that the HCI feedback loop correctly modifies the effective diffusion rate.

2.  **Integration Tests for `TechnologyManager`**:
    -   Modify `tests/systems/test_technology_manager.py`.
    -   Test the full **Sync → Process → Commit** cycle.
    -   Create mock `FirmTechInfoDTO` lists and verify that the NumPy arrays are built correctly.
    -   Verify that `get_productivity_multiplier` returns the correct aggregate value from the `adoption_matrix`.

3.  **Performance Benchmark**:
    -   Create a script `scripts/benchmark_tech_diffusion.py`.
    -   This script will initialize the `TechnologyManager` and run its `update` method in a loop for a simulation of 2,000 firms and 10 technologies over 500 ticks.
    -   Assert that the average time per tick is well below 1 second.

4.  **Test Refactoring**:
    -   Existing tests that target the logic within `TechnologyManager._process_diffusion` will be deprecated or refactored to test the new `TechnologySystem` instead.

## 8. Risk & Impact Audit (Mitigation Plan)

This design directly addresses the findings of the pre-flight audit:

1.  **Architectural Mismatch**: **Mitigated.** We are not replacing the `Firm` "God Class". The `TechnologySystem` is introduced as a separate, parallel system, and `TechnologyManager` acts as the data synchronization layer.
2.  **Algorithmic Mismatch**: **Mitigated.** The sequential `for` loop in `_process_diffusion` is specifically targeted and replaced by a series of broadcasted NumPy operations, as detailed in the pseudo-code.
3.  **Data Structure Incompatibility**: **Mitigated.** The `dict` of `sets` (`adoption_registry`) is explicitly replaced by a 2D boolean `adoption_matrix`. The plan acknowledges the need for `id_to_idx` mappings to bridge the object world and the array world.
4.  **Violation of State Immutability**: **Mitigated.** The new `TechnologySystem.update` method is designed to be pure. It takes arrays as input and returns a *new* array, with no side effects. The `TechnologyManager` is responsible for the "commit" phase, ensuring a clean separation of concerns.
5.  **Inevitable Test Invalidation**: **Addressed.** The "Verification Plan" explicitly allocates effort for unit testing the new system, integration testing the refactored manager, and creating a performance benchmark, while acknowledging that old tests will need refactoring.
