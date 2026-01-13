# WO-053: Phase 23 - The Industrial Revolution (Productivity Shock)

**Goal**: Break the Malthusian Trap by introducing exponential productivity growth via "Technology".
**Key Feature**: `TechnologyManager` & **Chemical Fertilizer** (Food Productivity 3x).

---

## 1. Background & Context
*   **Problem**: Phase 22 simulation crashed due to Malthusian Collapse (Extinction). Supply chain broke before population could rebound.
*   **Solution**: Introduce "Chemical Fertilizer" (Haber-Bosch Process) to decouple food production from linear labor growth.
*   **Phase**: 23 (The Great Expansion).

## 2. Core Specifications

### A. TechnologyManager (New System)
*   **Role**: Manages Global Technology State & Diffusion.
*   **Location**: `simulation/systems/technology_manager.py`
*   **Data Structure**:
    ```python
    @dataclass
    class TechNode:
        id: str
        name: str
        sector: str # e.g., "FOOD", "MANUFACTURING"
        multiplier: float # e.g., 3.0 (+200%)
        unlock_condition: Dict[str, Any] # e.g., {"tick": 200, "innovation_pool": 100}
        diffusion_rate: float # 0.0 ~ 1.0 (How fast it spreads to firms)
    ```

### B. The First Unlock: Chemical Fertilizer
*   **ID**: `TECH_AGRI_CHEM_01`
*   **Sector**: `FOOD`
*   **Effect**: Multiplies `productivity_factor` by **3.0**.
*   **Trigger**:
    *   **Option A (Simple)**: Time-based (e.g., Tick 100).
    *   **Option B (Dynamic)**: Total Population > X or Starvation Event occurred.
    *   *Decision*: Time-based (Tick 1500) or Manual Trigger via Spec. For now, **Tick 10** for immediate verification in test.

### C. Firm Integration
*   **Modify**: `Firm.produce()` in `simulation/firms.py`.
*   **Logic**:
    ```python
    # Before
    tfp = self.productivity_factor
    
    # After
    tech_mult = technology_manager.get_productivity_multiplier(self.sector, self.id)
    tfp = self.productivity_factor * tech_mult
    ```
*   **Diffusion Logic (The S-Curve)**:
    1.  **Unlock**: When tech unlocks, only `is_visionary` firms (or top 10% wealthy) adopt immediately.
    2.  **Spread**: Every tick, check unadopters.
        *   `prob = diffusion_rate` (Global parameter, e.g., 0.05).
        *   If `random < prob`: Adopt.
        *   Effect: Adoption curve follows Sigmoid function (Slow -> Fast -> Saturation).
    3.  **Result**: Productivity rises exponentially/logistically, preventing instant price crash shock.

## 3. Implementation Plan

### Step 1: Create `TechnologyManager`
*   Implement `TechnologyManager` class.
*   Define `TECH_TREE` config.

### Step 2: Integrate with Engine
*   Initialize `TechnologyManager` in `Scenario/Engine`.
*   Call `technology_manager.update(current_tick)` loop.

### Step 3: Firm Integration
*   Inject `technology_manager` into `Firm.produce` context (or `make_decision`).
*   Update TFP calculation.

## 4. Verification Plan (Iron Test)
*   **Scenario**: Run 200 tick simulation.
*   **Trigger**: At Tick 50, unlock `Chemical Fertilizer`.
*   **Expectation**:
    *   Step 1: Food Production jumps.
    *   Step 2: Food Price drops.
    *   Step 3: Population creates surplus + Growth.
    *   **No Extinction**.

## 5. Deliverables
1.  `simulation/systems/technology_manager.py`
2.  `tests/verify_industrial_revolution.py`
3.  Updated `simulation/firms.py`
