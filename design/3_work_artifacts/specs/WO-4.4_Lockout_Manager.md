# WO-4.4: PolicyLockoutManager & Action Tagging

**Status**: 🟢 Ready for Implementation (PR-Chunk #5)
**Target**: `modules/government/components/policy_lockout_manager.py`, `simulation/ai/enums.py`
**Goal**: Implement the "Scapegoat Mechanic" via policy tag cooldowns.

## 1. Scope of Work
- Implement `PolicyLockoutManager`.
- Tag all government actions with `PolicyActionTag`.
- Integrate into `Government` container.

## 2. Implementation Details

### 2.1. Lockout Manager
- Methods: `lock_policy(tag, duration)`, `is_locked(tag)`.
- Trigger: When `fire_advisor(school)` is called, lockout all associated tags for 20 ticks.

### 2.2. Government Integration
- Instantiate `PolicyLockoutManager` in `Government`.
- Ensure all policy methods (tax/spend) have associated tags.

## 3. Verification
- Call `fire_advisor(KEYNESIAN)`, verify `is_locked(KEYNESIAN_FISCAL)` is True for 20 ticks.
