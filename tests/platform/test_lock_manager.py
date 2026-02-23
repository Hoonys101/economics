import pytest
import os
import sys
from unittest.mock import MagicMock, patch, mock_open

from modules.platform.infrastructure.lock_manager import PlatformLockManager, LockAcquisitionError

class TestPlatformLockManager:

    def setup_method(self):
        self.lock_path = "test_simulation.lock"

    @patch('modules.platform.infrastructure.lock_manager.os.name', 'posix')
    @patch('modules.platform.infrastructure.lock_manager.fcntl')
    def test_acquire_unix_success(self, mock_fcntl):
        mock_fcntl.LOCK_EX = 2
        mock_fcntl.LOCK_NB = 4

        manager = PlatformLockManager(self.lock_path)
        with patch('builtins.open', mock_open()) as mock_file:
            manager.acquire()

            mock_fcntl.flock.assert_called_once()
            args = mock_fcntl.flock.call_args[0]
            # Verify lock flags (LOCK_EX | LOCK_NB)
            assert args[1] == (mock_fcntl.LOCK_EX | mock_fcntl.LOCK_NB)

    @patch('modules.platform.infrastructure.lock_manager.os.name', 'posix')
    @patch('modules.platform.infrastructure.lock_manager.fcntl')
    def test_acquire_unix_fail(self, mock_fcntl):
        mock_fcntl.LOCK_EX = 2
        mock_fcntl.LOCK_NB = 4
        mock_fcntl.flock.side_effect = IOError("Locked")

        manager = PlatformLockManager(self.lock_path)

        with patch('builtins.open', mock_open()) as mock_file:
            with pytest.raises(LockAcquisitionError):
                manager.acquire()

    @patch('modules.platform.infrastructure.lock_manager.os.name', 'nt')
    @patch('modules.platform.infrastructure.lock_manager.msvcrt', create=True)
    def test_acquire_windows_success(self, mock_msvcrt):
        mock_msvcrt.LK_NBLCK = 1

        manager = PlatformLockManager(self.lock_path)
        with patch('builtins.open', mock_open()) as mock_file:
            # Mock fileno()
            mock_file.return_value.fileno.return_value = 10

            manager.acquire()

            mock_msvcrt.locking.assert_called_once()
            # Verify lock flags (LK_NBLCK, 1 byte)
            args = mock_msvcrt.locking.call_args[0]
            assert args[0] == 10 # fd
            assert args[1] == mock_msvcrt.LK_NBLCK
            assert args[2] == 1

    @patch('modules.platform.infrastructure.lock_manager.os.name', 'nt')
    @patch('modules.platform.infrastructure.lock_manager.msvcrt', create=True)
    def test_acquire_windows_fail(self, mock_msvcrt):
        mock_msvcrt.LK_NBLCK = 1
        mock_msvcrt.locking.side_effect = IOError("Locked")

        manager = PlatformLockManager(self.lock_path)

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.return_value.fileno.return_value = 10

            with pytest.raises(LockAcquisitionError):
                manager.acquire()

    @patch('modules.platform.infrastructure.lock_manager.os.name', 'posix')
    @patch('modules.platform.infrastructure.lock_manager.fcntl')
    def test_release_unix(self, mock_fcntl):
        mock_fcntl.LOCK_EX = 2
        mock_fcntl.LOCK_NB = 4
        mock_fcntl.LOCK_UN = 8

        manager = PlatformLockManager(self.lock_path)
        with patch('builtins.open', mock_open()) as mock_file:
            manager.acquire()
            manager.release()

            mock_fcntl.flock.assert_called_with(mock_file.return_value, mock_fcntl.LOCK_UN)
            mock_file.return_value.close.assert_called()
