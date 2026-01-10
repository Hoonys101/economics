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
- [x] 14. Phase 17+: Market Diversity (Real Estate, Services, Raw Materials)
    - [x] 17-1: Service Market (Completed)
    - [x] 17-2: Raw Materials (Completed)
    - [x] 17-3a: Real Estate Rental (Completed)
    - [x] 17-3b: Real Estate Sales & Mortgage (Completed)
    - [x] 17-4: The Society of Vanity & Control (Completed)
    - [x] 17-5: The Leviathan (Completed)
- [x] 15. **Phase 19: Population Dynamics** (Birth Strike, Extinction Scenario)
    - [x] Task 1: Demographic Manager (Birth/Aging/Death System)
    - [x] Task 2: Evolutionary Decision Engine (r/K Strategy, Time Allocation)
    - [x] Task 3: Household Extensions (Education, Time Budget, Children)
    - [x] Task 4: Verification (The Rat Race Experiment Success)
- [x] 16. **Phase 20: The Matrix & Advanced Dynamics** (Completed)
    - [x] **Step 1: Cognitive Architecture (The Matrix Core)**
        - [x] Task 1.1: System 1 (Fast/RL) & System 2 (Slow/Planner) Integrated
        - [x] Task 1.2: Internal World Model (NPV Projection)
    - [x] **Step 2: Socio-Tech Dynamics**
        - [x] Task 2.1: Lactation & Appliance Dependency
        - [x] Task 2.2: Gender-Specific Education & Market Access
    - [x] **Step 3: Real Estate & Integration**
        - [x] Task 3.1: Supply Dynamics & Immigration Model
        - [x] Task 3.2: Scenario Verification (Housing Costs Impact)

- [x] **Step 3: Real Estate & Integration**
        - [x] Task 3.1: Supply Dynamics & Immigration Model
        - [x] Task 3.2: Scenario Verification (Housing Costs Impact)

## 🔭 Phase 20.5: The Simulation Cockpit (Stabilization)
- **Goal**: Visibility & God-Mode Control (UI).
- **Tech**: Streamlit.
- [ ] WO-037: Dashboard Scaffolding (Setup & Engine Bridge).
- [ ] WO-038: God Mode Controls (Sliders for Macro/Social/Tech).
- [ ] WO-039: Deep Dive Analytics (System 2 Logs & Heatmaps).

## 🔮 Phase 21+: The Future Visions (Long-Term)

### Vision A: The Political Animal (Politics & Democracy)
- **Goal**: Introduce Voting Power and Democracy.
- **Scenario**: 
    - Renters vote for Rent Control & Subsidies.
    - Owners vote for Tax Cuts & Asset Protection.
    - Simulation of Gerontocracy (Rule of the Old) vs Youth Disenchantment.

### Vision B: Corporate Empires (Corporate AI Adoption)
- **Goal**: Upgrade Firms to Active AI Agents.
- **Scenario**:
    - Firms invest in Automation to combat Labor Scarcity (Phase 20 result).
    - Resulting Unemployment vs Productivity Gains.
    - Rise of Monopolies and "Too Big To Fail".

### Vision C: The Central Bank (Macro Control Tower)
- **Goal**: User-in-the-loop Macroeconomic Control.
- **Scenario**:
    - User (President/Governor) sets Interest Rates & Tax Policy.
    - AI-based Policy Optimization (RL Government).
    - Crisis Management Mode (Great Depression/Hyperinflation).
- [ ] 17. Commercial Bank Deepening (Lender of Last Resort)
- [ ] 18. Time Machine (Backtester)
- [ ] 21. **Config Refactoring Pass 2**: 런타임 조정 시스템 (CLI/API 연동)

## ⚠️ [MAJOR OVERHAUL REQUIRED] Cognitive Architecture (Phase 20+)
> **Goal**: System 1 (Fast/RL) + System 2 (Slow/Planner) 분리
> **Trigger**: 부동산/연금 등 초장기 결정이 필요한 기능 확장 시
> **Reference**: Kahneman's Dual-Process Theory

- **Current State**: RL(Q-Learning)은 단기 보상에만 반응 (근시안적).
- **Future State**: Model-Based Planning을 통해 미래 시나리오를 시뮬레이션하고 현재 행동을 제약.
- **Interim Solution**: Phase 17-3에서는 `HousingManager`가 NPV 계산으로 대리 수행.

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
