# WO-4.5: AdaptiveGovBrain & Decision Cycle

**Status**: 🟢 Ready for Implementation (PR-Chunk #6)
**Target**: `modules/government/policies/adaptive_gov_brain.py`, `simulation/agents/government.py`
**Goal**: Implement the utility-driven decision engine for the government.

## 1. Scope of Work
- Create `AdaptiveGovBrain`.
- Implement "Propose-Filter-Execute" cycle in `Government`.
- Define party-specific utility functions.

## 2. Implementation Details

### 2.1. AdaptiveGovBrain
- `propose_actions(state)`: Returns `List[PolicyActionDTO]` with utility scores.
- **RED Utility**: $U = 0.7 \cdot LowAssetApproval + 0.3 \cdot GiniImprovement$
- **BLUE Utility**: $U = 0.6 \cdot HighAssetApproval + 0.4 \cdot GDPGrowth$

### 2.2. Government Refactoring
- `make_policy_decision()`:
  1.  `Brain.propose_actions()`
  2.  `LockoutManager.filter_actions()`
  3.  `Softmax(utility)` selection.
  4.  Execute chosen action.

## 3. Verification
- Verify RED party prioritizes welfare when Inequality is high.
- Verify selection probability for locked actions is 0.
