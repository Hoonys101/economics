# Specification: Wave 5 Government AI (Populist Brain)

## 1. Overview
The **Government AI** is the decision-making core of the Smart Leviathan. In Wave 5, it evolves from a benevolent technocrat (optimizing solely for GDP/Stability) into a **Political Animal**. It seeks to maximize **Public Approval** and **Regime Survival**, learning to trade off long-term economic health for short-term voter satisfaction when necessary.

## 2. Core Mandates
1.  **Populist Objective**: The primary maximization target is `overall_approval_rating`.
2.  **Survival Constraint**: The secondary target is avoiding "State Failure" (Hyperinflation or Depression), which results in a hard game-over penalty.
3.  **Expanded Consciousness**: The AI must perceive `Approval` and `Lobbying Pressure` as first-class state variables.
4.  **Continuous Learning**: The AI updates its strategy every `ACTION_INTERVAL` (30 ticks) based on the *current* polling data, not just election results.

## 3. Detailed Design

### 3.1. State Space (The 6-Tuple)
The AI perceives the world through 6 discrete dimensions (Total 729 States):

| Dimension | Discrete Levels (0, 1, 2) | Logic / Thresholds |
| :--- | :--- | :--- |
| **Inflation** | Low / Target / High | Target ± 1.0% |
| **Unemployment** | Low / Target / High | Target ± 1.0% |
| **GDP Growth** | Recession / Stagnant / Boom | < -0.5% / -0.5~2% / > 2% |
| **Debt Ratio** | Low / Sustainable / Crisis | < 40% / 40-80% / > 80% |
| **Approval** | **Danger / Safe / Hero** | **< 40% / 40-60% / > 60%** |
| **Lobbying** | **Neutral / Corp / Labor** | **Net Pressure Direction** |

#### 3.1.1. Lobbying State Logic
-   **Corp (1)**: High pressure to *Lower Corporate Tax* or *Increase Subsidies*.
-   **Labor (2)**: High pressure to *Increase Welfare* or *Lower Income Tax*.
-   **Neutral (0)**: Pressure balanced or negligible.

### 3.2. Reward Function (The "Vote-Seeker" Equation)
The reward $R$ is calculated as:

$$
R = (w_{app} \times R_{approval}) + (w_{stab} \times R_{stability}) + (w_{lob} \times R_{lobbying})
$$

Where:
-   **$R_{approval}$**: $(ApprovalRating - 0.5) \times 100$.
    -   Range: -50 to +50.
    -   Encourages keeping approval > 50%.
-   **$R_{stability}$**: $- (InflationGap^2 + UnemploymentGap^2) \times 50$.
    -   Penalty only. Punishes deviation from macro targets.
-   **$R_{lobbying}$**: $+10$ if Action aligns with Lobbying Pressure.
    -   Example: If State is `Corp_Pressure` and Action is `Fiscal_Ease` (Cut Tax), add bonus.

**Default Weights**:
-   `w_approval`: 0.7 (Primary driver)
-   `w_stability`: 0.3 (Constraint)
-   `w_lobbying`: 0.1 (Tie-breaker/Nudge)

### 3.3. Learning Loop & Versioning

#### 3.3.1. Q-Table Management
-   **Filename**: `q_table_v5_populist.pkl`
-   **Initialization**: If file missing or shape mismatch (4-tuple vs 6-tuple), init new table with small random noise.

#### 3.3.2. The Feedback Cycle
1.  **Tick T**: `decide_policy()` observes $S_t$, chooses $A_t$.
2.  **Tick T+1...T+29**: Economy reacts. `PoliticalOrchestrator` aggregates votes/lobbying.
3.  **Tick T+30**: `update_learning()` called.
    -   Calculate $R_{t+30}$ based on *current* Approval and Stability.
    -   Update $Q(S_t, A_t)$.
    -   Set $S_{t+1}$ as new current state.

### 3.4. Reflex Override (Constitutional Constraint)
The rigid `REFLEX_OVERRIDE` in `SmartLeviathanPolicy` will be wrapped in a config check:

```python
if self.config.enable_reflex_override and inflation_state == 2:
    action = ACTION_HAWKISH
```

For Wave 5, `enable_reflex_override` defaults to **False**. We want to see if the AI *learns* that hyperinflation eventually kills approval (via purchasing power loss) and thus chooses Hawkishness voluntarily.

## 4. Verification Plan

### 4.1. Unit Tests
-   **`test_reward_function_populism`**:
    -   Scenario: Inflation High, Approval Low.
    -   Compare Reward of `Fiscal_Ease` (Stimulus) vs `Hawkish` (Austerity).
    -   Verify `Fiscal_Ease` yields higher immediate reward if `w_approval` is high, despite stability penalty.
-   **`test_state_discretization_v5`**:
    -   Inject `GovernmentStateDTO` with `approval=0.3` (Danger).
    -   Verify `_get_state()` returns tuple with 5th element `0`.
-   **`test_lobbying_bonus`**:
    -   Scenario: `Lobbying=Corp` (State 1).
    -   Action: `Fiscal_Ease`.
    -   Verify Reward is higher than same scenario with `Lobbying=Neutral`.

### 4.2. Integration Tests
-   **"The Pandering Loop"**:
    -   Run simulation. Force `Household` agents to vote based solely on "Welfare Payments".
    -   Observe if Government AI learns to maximize Welfare to 100% budget, disregarding debt/inflation.
    -   *Success Criteria*: AI discovers the "Populist Optima" (High Welfare) within 50 epochs.

### 4.3. Impact Analysis
-   **Breaking Changes**: The `GovernmentAI` class signature and `q_table` format are changing. All tests mocking `GovernmentAI` must be updated.
-   **Mitigation**: Create `GovernmentAI_V4` class for backward compatibility if needed, or simply update all mocks if V4 is deprecated (Recommended: Deprecate V4).
