# Technical Insight Report: WO-136 Clean Sweep Generalization

## 1. Problem Phenomenon
The original implementation of the `TechnologyManager` relied on Python loop-based logic for technology diffusion. While functional for small agent counts (N < 500), this approach scales linearly O(N*M) where N is the number of firms and M is the number of technologies.

Symptoms included:
- Potential performance degradation in large-scale scenarios (e.g., 2000+ agents).
- `_process_diffusion` method iterating through every firm and performing multiple dictionary lookups (`adoption_registry`).
- Lack of vectorized operations preventing the use of efficient numerical libraries like Numpy.

## 2. Root Cause Analysis
The bottleneck was identified in the `TechnologyManager._process_diffusion` method:
1. **Data Structure**: `adoption_registry` was a `Dict[int, Set[str]]`. Checking adoption required a hash lookup for every firm-tech pair every tick.
2. **Algorithm**: List comprehensions were used to build masks (`already_adopted_mask`), resulting in explicit Python loops.
3. **Architecture**: Lack of separation between high-frequency numerical operations (diffusion) and object-oriented agent state.

## 3. Solution Implementation Details
The solution involved a complete refactor of the `TechnologyManager` to a vectorized architecture:

1.  **Adoption Matrix (`numpy.ndarray`)**:
    - Replaced the dictionary-based registry with a boolean matrix `self.adoption_matrix` of shape `(max_firm_id + 1, num_techs)`.
    - This allows O(1) adoption checks via direct indexing `matrix[firm_ids, tech_idx]`.

2.  **Vectorized Logic**:
    - `_process_diffusion` now converts firm lists to Numpy arrays once.
    - All filtering (Sector match, Adoption check, Probability roll) is done using vectorized boolean masking.
    - `np.random.rand` generates all random numbers in a single call.

3.  **Dynamic Resizing**:
    - Implemented `_ensure_capacity(max_firm_id)` to automatically resize the matrix as new firms are created (e.g., via cloning or IPOs), ensuring robustness.

4.  **R&D Bridge**:
    - Implemented `Firm.get_tech_info()` to expose `current_rd_investment` via a pure DTO (`FirmTechInfoDTO`), decoupling the simulation engine from the full `Firm` object during the tech phase.

## 4. Lessons Learned & Technical Debt
-   **Insight**: Numpy vectorization is critical for "System 1" (fast, unconscious) simulation processes like diffusion, allowing Python to act as an orchestrator rather than a calculation engine.
-   **Technical Debt Identified**:
    -   **Firm ID Continuity**: The matrix approach assumes Firm IDs are relatively dense. If IDs become extremely sparse (e.g., random 64-bit integers), the matrix size would be prohibitive. A mapping layer (`id_to_index`) might be needed in the future if ID generation strategy changes.
    -   **Memory Usage**: While currently negligible (10k agents * 10 techs = 100k bits), extremely large simulations might require sparse matrices (`scipy.sparse`).
    -   **Strict Typing**: The bridge between `Firm` (OO) and `TechnologyManager` (Vector) relies on DTOs. Ensuring these DTOs remain lightweight is key to performance.
