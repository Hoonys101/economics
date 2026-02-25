import os
import sys
import time
import pytest
import logging
from multiprocessing import Process, Event
from modules.platform.infrastructure.lock_manager import PlatformLockManager, LockAcquisitionError

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def hold_lock(event_ready, event_stop, lock_file):
    """
    Function run in a separate process to hold the lock.
    """
    manager = PlatformLockManager(lock_file)
    try:
        manager.acquire()
        event_ready.set()
        event_stop.wait()
    except Exception as e:
        print(f"Child process failed to acquire lock: {e}")
    finally:
        manager.release()

@pytest.mark.no_lock_mock
class TestLockManagerRobustness:

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.lock_file = "test_simulation.lock"
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
        self.manager = PlatformLockManager(self.lock_file)
        yield
        if self.manager._lock_file:
            self.manager.release()
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except PermissionError:
                pass # Windows might hold it briefly

    def test_acquire_creates_pid_file(self):
        """Verify that acquiring the lock writes the current PID."""
        self.manager.acquire()
        self.manager.release()

        assert os.path.exists(self.lock_file)
        with open(self.lock_file, 'r') as f:
            content = f.read().strip()

        assert content == str(os.getpid())

    def test_recover_stale_lock_file(self):
        """Verify that we can acquire a lock even if a stale file exists (orphaned lock file)."""
        # Create a stale lock file with a non-existent PID
        with open(self.lock_file, 'w') as f:
            f.write("99999")

        # Try to acquire
        try:
            self.manager.acquire()
        except LockAcquisitionError:
            pytest.fail("Should have acquired lock despite stale file (OS lock was free)")

        self.manager.release()

        # Verify new PID is written
        with open(self.lock_file, 'r') as f:
            content = f.read().strip()
        assert content == str(os.getpid())

    def test_fail_on_active_lock(self):
        """Verify that we fail to acquire if another process holds the lock."""
        event_ready = Event()
        event_stop = Event()

        p = Process(target=hold_lock, args=(event_ready, event_stop, self.lock_file))
        p.start()

        # Wait for child to acquire lock
        if not event_ready.wait(timeout=5):
            p.terminate()
            pytest.fail("Child process failed to acquire lock in time")

        try:
            # Try to acquire in main process
            with pytest.raises(LockAcquisitionError) as excinfo:
                self.manager.acquire()

            # Optional: verify message contains PID info?
            # Since we can't easily get the child PID via 'hold_lock' without it writing it first.
            # But the child *did* write it (because of our changes).
            # So the error message *should* contain the child PID.
            # But p.pid is available here.

            # The error message should imply "Simulation is already running (PID {p.pid})"
            error_msg = str(excinfo.value)
            assert str(p.pid) in error_msg or "Locked by another process" in error_msg

        finally:
            event_stop.set()
            p.join()
