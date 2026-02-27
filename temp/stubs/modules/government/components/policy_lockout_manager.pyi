from _typeshed import Incomplete
from simulation.ai.enums import PolicyActionTag as PolicyActionTag

logger: Incomplete

class PolicyLockoutManager:
    """
    Manages the 'Scapegoat Mechanic' for government policies.
    When a political advisor is fired, associated policies are locked out for a duration.
    This prevents the government from immediately re-adopting policies associated with a failed advisor.
    """
    def __init__(self) -> None: ...
    def lock_policy(self, tag: PolicyActionTag, duration: int, current_tick: int) -> None:
        """
        Locks a policy tag until current_tick + duration.
        If already locked, extends the lock if the new end time is later.

        Args:
            tag: The policy tag to lock.
            duration: Number of ticks the lock should last.
            current_tick: The current simulation tick.
        """
    def is_locked(self, tag: PolicyActionTag, current_tick: int) -> bool:
        """
        Checks if a policy tag is currently locked.

        Args:
            tag: The policy tag to check.
            current_tick: The current simulation tick.

        Returns:
            True if the policy is locked, False otherwise.
        """
    def get_lockout_end_tick(self, tag: PolicyActionTag) -> int | None:
        """Returns the tick when the lockout expires, or None if not locked."""
