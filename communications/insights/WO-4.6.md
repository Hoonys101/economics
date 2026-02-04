# WO-4.6: Leviathan Macro Scenarios Insights

**Status**: 🟢 Verified
**Test File**: `tests/scenarios/test_leviathan_emergence.py`

## 1. Scapegoat Emergence
- **Mechanism**: The `AdaptiveGovBrain` includes a `FIRE_ADVISOR` action as a candidate policy.
- **Trigger**: `FIRE_ADVISOR` is only effective (positive utility) when approval is critically low (< 0.4). In this state, it provides a +0.20 approval boost (simulating blame shifting).
- **Result**: In the test, with approval at 0.1, the system successfully selected `FIRE_ADVISOR`, which called `Government.fire_advisor(KEYNESIAN)`, resulting in `PolicyActionTag.KEYNESIAN_FISCAL` being locked for 20 ticks.
- **Implication**: The system demonstrates "Blame Avoidance" behavior emerging from utility maximization during crisis, but correctly avoids it during normal times (where it would look desperate).

## 2. Paradox Support Emergence
- **Mechanism**: The `PoliticalComponent` logic weighs `Ideological Match` (0.6) higher than `Satisfaction` (0.4) for approval calculation.
- **Scenario**: A `GROWTH_ORIENTED` household (Vision ~0.9) matches perfectly with the `BLUE` party (Stance 0.9).
- **Result**: Even when the household is poor (High Survival Need -> Low Satisfaction), the strong ideological alignment keeps the approval rating positive (1).
- **Observation**: Test verified that a poor household with `GROWTH_ORIENTED` personality maintains support for the `BLUE` party.
- **Implication**: This validates the "Voting Against Economic Interest" phenomenon based on cultural/ideological alignment.

## 3. Political Business Cycle Emergence
- **Mechanism**: The `AdaptiveGovBrain` monitors the election cycle (`tick % 100`). When the election is near (`>= 80`), the utility function weights shift to prioritize **Approval** (0.9 weight) over other metrics like GDP or Equality.
- **Scenario**: At tick 90 (Election Near), a Blue Government with moderate approval (0.5).
- **Result**: The brain selects `Tax Cut (Corp)` (or Fiscal Stimulus) because it provides the highest immediate approval boost (+0.04), outcompeting "Do Nothing" or Austerity.
- **Observation**: Test verified that near election time, the government switches to expansionary policy to secure votes.
- **Implication**: The Political Business Cycle emerges naturally from the shifting incentives of the ruling party as the election approaches.

## 4. Technical Debt / Future Work
- **Fire Advisor Target**: Currently, `FIRE_ADVISOR` defaults to firing the `KEYNESIAN` advisor. Future iterations should dynamically select the advisor based on which policies were recently active or failed.
- **Brain Calibration**: The utility weights and prediction deltas are heuristic. They should ideally be tuned or learned via RL in Phase 24+.
- **Election Awareness**: Currently `tick % 100` is hardcoded in the brain. It should ideally be a property of `GovernmentStateDTO` (e.g., `ticks_until_election`).
