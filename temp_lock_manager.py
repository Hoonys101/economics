import os
import sys
import logging
from typing import Optional, TextIO

# Platform-specific imports
if os.name == 'nt':
    try:
        import msvcrt
        import ctypes
    except ImportError:
        msvcrt = None
        ctypes = None
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
    Now includes PID verification and writing.
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
            # Before attempting to open/lock, check if there's a stale lock
            # that needs to be cleared (e.g., process died without releasing).
            try:
                self._check_lock_status()
            except LockAcquisitionError:
                # Still running, handle below or let it raise here?
                # Actually _check_lock_status raises if it IS running. If it's stale, it returns.
                pass

            # Use 'a+' (append+read) to handle both checking stale content and overwriting
            self._lock_file = open(self.lock_file_path, 'a+')
        except PermissionError:
            # On Windows, opening a locked file with 'a+' can raise PermissionError
            try:
                self._check_lock_status()
            except LockAcquisitionError as le:
                raise le
            raise LockAcquisitionError("Simulation is already running (Locked by another process)")
        except IOError as e:
            raise LockAcquisitionError(f"Could not open lock file: {e}")

        try:
            if os.name == 'nt':
                self._acquire_windows()
            else:
                self._acquire_unix()

            # If successful, write PID
            self._update_lock_file()
            self.logger.info(f"Acquired exclusive lock on {self.lock_file_path}")

        except LockAcquisitionError as e:
            # Check if this is a stale lock or valid lock
            self._check_lock_status()
            # If check_lock_status doesn't raise (it re-raises with more info usually), we re-raise original
            raise e

    def _update_lock_file(self) -> None:
        """Truncates the file and writes the current PID."""
        if not self._lock_file:
            return
        try:
            self._lock_file.seek(0)
            self._lock_file.truncate()
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()
            try:
                os.fsync(self._lock_file.fileno())
            except (OSError, AttributeError, TypeError):
                # fsync might fail on some pipe-like files or mocks
                pass
        except IOError as e:
            self.logger.error(f"Failed to write PID to lock file: {e}")

    def _check_lock_status(self) -> None:
        """
        Reads the PID from the lock file and checks if the process is running.
        Raises LockAcquisitionError with detailed info if active.
        Clears the lock file if it is stale.
        """
        try:
            if not os.path.exists(self.lock_file_path):
                 return

            # Open a new handle to read, since the original one is closed/failed
            try:
                with open(self.lock_file_path, 'r') as f:
                    content = f.read().strip()
            except PermissionError:
                raise LockAcquisitionError("Simulation is already running (Locked by another process)")

            if not content:
                 return

            try:
                pid = int(content)
            except ValueError:
                self.logger.warning(f"Invalid PID in lock file: '{content}'")
                return

            if self._is_process_running(pid):
                raise LockAcquisitionError(f"Simulation is already running (PID {pid})")
            else:
                # PID found, but not running. Stale lock.
                self.logger.warning(f"Stale lock detected for PID {pid}. Process is not running. Clearing stale lock.")
                try:
                    os.remove(self.lock_file_path)
                    self.logger.info("Cleared stale lock file.")
                except OSError as e:
                    self.logger.warning(f"Could not remove stale lock file: {e}")
                # We return without error so caller can proceed to acquire lock.

        except IOError:
            pass # Can't read file

    def _is_process_running(self, pid: int) -> bool:
        """Checks if a process with the given PID is running."""
        try:
            if os.name == 'nt':
                if not ctypes:
                    return True # Fallback assume running if no ctypes

                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_INFORMATION = 0x0400
                SYNCHRONIZE = 0x00100000

                process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | SYNCHRONIZE, False, pid)
                if process:
                    exit_code = ctypes.c_ulong()
                    if kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                        kernel32.CloseHandle(process)
                        return exit_code.value == 259 # STILL_ACTIVE = 259
                    kernel32.CloseHandle(process)
                return False
            else:
                # Unix: sending signal 0 checks existence
                os.kill(pid, 0)
                return True
        except OSError:
            return False
        except Exception:
            return False

    def _acquire_windows(self) -> None:
        if not msvcrt:
             # Robustness Fix: Fail loudly if locking primitives are missing
             raise LockAcquisitionError("msvcrt module not found on Windows. Locking unavailable.")

        try:
            # LK_NBLCK: Non-blocking lock
            # Lock 1 byte at the beginning of the file
            # Robustness Fix: Seek to 0 to ensure consistent locking region regardless of file mode (a+)
            self._lock_file.seek(0)
            fd = self._lock_file.fileno()
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except IOError:
            self._cleanup()
            raise LockAcquisitionError("Simulation is already running (Windows lock).")

    def _acquire_unix(self) -> None:
        if not fcntl:
             # Robustness Fix: Fail loudly if locking primitives are missing
             raise LockAcquisitionError("fcntl module not found on Unix. Locking unavailable.")

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
