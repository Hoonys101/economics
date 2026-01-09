# Prioritized Improvement Roadmap (Delegated to Jules)

## 🟢 Low Risk: Stability & Visualization
- [x] 1. Type Stability (Fix 13+ Mypy Errors)
- [ ] 2. Edge Case Testing (Disaster Scenario Suite)
- [ ] 3. Market Network Visualization (UI Dependency)

## 🟡 Medium Risk: Agent Logic & Tuning
- [ ] 4. Mitosis Mechanism Verification & Tuning
- [ ] 5. Social Inheritance (Child-Parent state transfer)
- [ ] 6. Advanced Needs Hierarchy (Maslow's model)

## 🔵 Completed / Integrated (Recent Phases)
- [x] 7. Brand Value & Product Quality Differentiation (Phase 6)
- [x] 8. Adaptive Price Expectations (Phase 8)
- [x] 9. Corporate M&A (Phase 9)
- [x] 10. Monetary Policy (Phase 10)
- [x] 11. Portfolio Optimization (Phase 16)
- [x] 12. Corporate Intelligence (Phase 16-B)
- [x] 13. Stock Exchange (Phase 14-4)

## 🔴 Pending / Future
- [ ] 14. Phase 17+: Market Diversity (Real Estate, Services, Raw Materials)
- [ ] 15. Commercial Bank Deepening (Lender of Last Resort)
- [ ] 16. Data Lake & Universe Expansion
- [ ] 17. Time Machine (Backtester)

## 🟣 Architecture v3.0: High-Performance Simulation (Long-Term)
> **Goal**: Optimization Strategy for 100k+ Agents (OOP -> DOP Transition)
> **Advisor**: Architect Prime

### 1. Philosophy: OOP to DOP (Data-Oriented Programming)
- **Problem**: `for agent in agents: agent.step()` is the bottleneck due to Python overhead and cache misses.
- **Solution**: Maximizing SIMD (Single Instruction, Multiple Data) and vectorized operations.

### 2. Implementation Stages
#### Stage 1: JIT Compilation (Low Effort, High Gain)
- **Action**: Apply `@numba.jit` to math-heavy functions (utility calc, tax calc).
- **Benefit**: 10x~50x speedup for computational hotspots without structural changes.

#### Stage 2: Profiling & Vectorized Decisions (The "Think" Layer)
- **Action**: Profile via `cProfile` to find bottlenecks.
- **Action**: Convert agent decision logic (Labor, Consumption) to **Vectorized Operations** using NumPy/Pandas.
    ```python
    # Example: Vectorized Labor Decision
    labor_supply = np.where(assets > threshold, 0, 8)
    ```
- **Benefit**: 100x speedup for decision phase (Parallelizable).

#### Stage 3: Batch Transaction Matching (The "Act" Layer)
- **Problem**: Sequential transactions handling resource contention.
- **Solution**: **Batch Matching** via Matrix Operations.
    - Construct `Demand Matrix` and `Supply Matrix`.
    - Use Linear Algebra (MatMul) to calculate utility scores.
    - Resolve contention via Pro-rata or Random Vectorized choices.

#### Stage 4: Entity Component System (ECS) (Final Form)
- **Action**: Replace Agent Classes with a monolithic **DataFrame/Database** (State Table).
- **Reference**: Standard pattern in Game Development (Data-Driven Design).
