import os
import sys
import logging
from typing import Optional, TextIO

# Platform-specific imports
if os.name == 'nt':
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
else:
    try:
        import fcntl
    except ImportError:
        fcntl = None

from modules.platform.api import ILockManager, LockAcquisitionError

class PlatformLockManager(ILockManager):
    """
    Cross-platform implementation of file locking.
    Uses 'fcntl' on Unix-like systems and 'msvcrt' on Windows.
    """

    def __init__(self, lock_file_path: str = 'simulation.lock'):
        self.lock_file_path = lock_file_path
        self._lock_file: Optional[TextIO] = None
        self.logger = logging.getLogger(__name__)

    def acquire(self) -> None:
        """
        Acquires an exclusive, non-blocking lock.
        Raises LockAcquisitionError if failed.
        """
        if self._lock_file:
            return # Already acquired

        try:
            # Use 'a' (append) to avoid truncating the file if it exists and has content (e.g. PID)
            self._lock_file = open(self.lock_file_path, 'a')
        except IOError as e:
            raise LockAcquisitionError(f"Could not open lock file: {e}")

        if os.name == 'nt':
            self._acquire_windows()
        else:
            self._acquire_unix()

        self.logger.info(f"Acquired exclusive lock on {self.lock_file_path}")

    def _acquire_windows(self) -> None:
        if not msvcrt:
             self.logger.warning("msvcrt module not found on Windows. Locking disabled.")
             return

        try:
            # LK_NBLCK: Non-blocking lock
            # Lock 1 byte at the beginning of the file
            fd = self._lock_file.fileno()
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except IOError:
            self._cleanup()
            raise LockAcquisitionError("Simulation is already running (Windows lock).")

    def _acquire_unix(self) -> None:
        if not fcntl:
             self.logger.warning("fcntl module not found on Unix. Locking disabled.")
             return

        try:
            # LOCK_EX: Exclusive
            # LOCK_NB: Non-blocking
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            self._cleanup()
            raise LockAcquisitionError("Simulation is already running (Unix lock).")

    def release(self) -> None:
        """
        Releases the lock and closes the file.
        """
        if not self._lock_file:
            return

        try:
            if os.name == 'nt':
                if msvcrt:
                    fd = self._lock_file.fileno()
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                if fcntl:
                    fcntl.flock(self._lock_file, fcntl.LOCK_UN)
        except IOError:
            self.logger.warning("Error releasing lock.")
        finally:
            self._cleanup()
            self.logger.info(f"Released lock on {self.lock_file_path}")

    def _cleanup(self) -> None:
        if self._lock_file:
            try:
                self._lock_file.close()
            except IOError:
                pass
            self._lock_file = None
