# SPEC: Operation Clean Sweep Refinement (Track 2)

## 1. Objective
Bridge individual firm R&D investment to global technology unlocks and optimize technology diffusion for high-performance scaling (2,000+ agents).

## 2. Architectural Solution

### 2.1. R&D Integration Bridge
- **Encapsulation**: `Firm` exposes `get_tech_info() -> FirmTechInfoDTO` containing `current_rd_investment`.
- **Orchestration**: `Simulation.run_tick` aggregates these DTOs and passes them to `TechnologyManager.update`.

### 2.2. Performance (Numpy Vectorization)
- **Data Structure**: `TechnologyManager` refactors `adoption_registry` to a 2D `numpy.bool_` matrix (`[firm_idx, tech_idx]`).
- **Algorithm**: `_process_diffusion` performs O(1) vectorized rolls against the matrix.

## 3. Implementation Checklist
- [ ] Add `get_tech_info()` to `Firm.py`.
- [ ] Update simulation orchestrator to aggregate and pass R&D data.
- [ ] Refactor `TechnologyManager` to use `adoption_matrix` (2D Numpy).
- [ ] Rewrite `_process_diffusion` for full vectorization.
- [ ] Create performance benchmark `scripts/bench_tech.py`.

## 4. Verification
- Benchmark: Average tick time for 2k agents < 10ms.
- Integration: Firms' R&D spending correctly triggers tech unlocks in logs.
