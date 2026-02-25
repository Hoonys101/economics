from typing import Protocol

class LockAcquisitionError(Exception):
    """Raised when a file lock cannot be acquired (e.g., another instance is running)."""

class ILockManager(Protocol):
    """
    Abstract interface for handling file-based concurrency locking.
    Must support both Windows (msvcrt) and Unix (fcntl).
    """
    def acquire(self) -> None:
        """
        Acquires an exclusive, non-blocking lock on the configured resource.
        Raises LockAcquisitionError if the lock is already held.
        """
    def release(self) -> None:
        """
        Releases the held lock and closes any underlying file handles.
        """
