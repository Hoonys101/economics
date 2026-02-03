# WO-4.6: Leviathan Macro Scenarios

**Status**: 🟢 Ready for Implementation (PR-Chunk #7)
**Target**: `tests/scenarios/test_leviathan_emergence.py`
**Goal**: Final verification of emergent political phenomena.

## 1. Scope of Work
- Implement Scapegoat Test.
- Implement Paradox Support Test.
- Implement Political Business Cycle Test.

## 2. Scenario Details

### 2.1. Scapegoat Test
- Force approval < 20%.
- Assert `fire_advisor` is eventually called.
- Assert subsequent action tags are locked.

### 2.2. Paradox Support Test
- Create poor households with `Personality.GROWTH_ORIENTED`.
- Assert high approval for BLUE party despite negative income growth.

## 3. Verification
- Run via `pytest tests/scenarios/test_leviathan_emergence.py`.
