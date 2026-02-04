from typing import Dict, List, Optional
import logging
from simulation.ai.enums import PolicyActionTag

logger = logging.getLogger(__name__)

class PolicyLockoutManager:
    """
    Manages the 'Scapegoat Mechanic' for government policies.
    When a political advisor is fired, associated policies are locked out for a duration.
    This prevents the government from immediately re-adopting policies associated with a failed advisor.
    """

    def __init__(self):
        # Maps PolicyActionTag to the tick number when the lock expires (exclusive)
        self._lockouts: Dict[PolicyActionTag, int] = {}

    def lock_policy(self, tag: PolicyActionTag, duration: int, current_tick: int) -> None:
        """
        Locks a policy tag until current_tick + duration.
        If already locked, extends the lock if the new end time is later.

        Args:
            tag: The policy tag to lock.
            duration: Number of ticks the lock should last.
            current_tick: The current simulation tick.
        """
        lock_end = current_tick + duration
        current_end = self._lockouts.get(tag, -1)

        if lock_end > current_end:
            self._lockouts[tag] = lock_end
            logger.info(f"POLICY_LOCKOUT | Locked {tag.name} until tick {lock_end} (Duration: {duration})")

    def is_locked(self, tag: PolicyActionTag, current_tick: int) -> bool:
        """
        Checks if a policy tag is currently locked.

        Args:
            tag: The policy tag to check.
            current_tick: The current simulation tick.

        Returns:
            True if the policy is locked, False otherwise.
        """
        if tag not in self._lockouts:
            return False

        is_active = current_tick < self._lockouts[tag]
        if not is_active and tag in self._lockouts:
             # Clean up expired lock (optional, but keeps dict clean)
             # However, keeping it might be useful for history.
             # Let's keep it simple and just return the check.
             pass

        return is_active

    def get_lockout_end_tick(self, tag: PolicyActionTag) -> Optional[int]:
        """Returns the tick when the lockout expires, or None if not locked."""
        return self._lockouts.get(tag)
