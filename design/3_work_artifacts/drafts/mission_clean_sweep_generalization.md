# Mission Guide: Clean Sweep Generalization (Track B)

## 1. Objective
Bridge individual firm R&D to global tech unlocks and vectorize the technology diffusion engine for high-performance scaling.

## 2. Reference Context
- [WO-136_CLEAN_SWEEP_REFINED.md](file:///c:/coding/economics/design/3_work_artifacts/specs/WO-136_CLEAN_SWEEP_REFINED.md)
- [Clean Sweep Original Spec](file:///c:/coding/economics/design/3_work_artifacts/specs/WO-136_Clean_Sweep_Spec.md)

## 3. Scope of Work (Focused)
- **R&D Bridge**: Implement `Firm.get_tech_info()` and aggregate R&D spending in the simulation core.
- **TechnologyManager Refactor**: Transition `adoption_registry` to a 2D Numpy matrix and vectorize `_process_diffusion`.
- **Benchmarking**: Create `scripts/bench_tech.py` and hit <10ms target.

## 4. Constraint (Purity)
- Do NOT modify `DashboardService` or `Tracker` (SMA) logic in this mission.
- Maintain O(1) vectorized operations as specified in the refined spec.
