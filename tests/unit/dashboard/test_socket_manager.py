import unittest
from unittest.mock import patch, ANY
import queue
import time
from simulation.dtos.commands import GodCommandDTO
import dashboard.services.socket_manager

class TestSocketManager(unittest.TestCase):

    def tearDown(self):
        # Reset singleton
        from dashboard.services.socket_manager import SocketManager
        if SocketManager._instance:
            SocketManager._instance._stop_event.set()
            SocketManager._instance = None

    @patch('dashboard.services.socket_manager.threading.Thread')
    def test_initialization(self, mock_thread):
        from dashboard.services.socket_manager import SocketManager
        # Clear singleton
        SocketManager._instance = None

        manager = SocketManager()
        self.assertTrue(manager._initialized)
        mock_thread.assert_called_once()
        self.assertEqual(manager.connection_status, "Disconnected")

    @patch('dashboard.services.socket_manager.threading.Thread')
    def test_send_command(self, mock_thread):
        from dashboard.services.socket_manager import SocketManager
        SocketManager._instance = None
        manager = SocketManager()

        cmd = GodCommandDTO(
            target_domain="Test",
            parameter_key="param",
            new_value=123
        )
        manager.send_command(cmd)

        self.assertFalse(manager.command_queue.empty())
        self.assertEqual(manager.command_queue.get(), cmd)

    @patch('dashboard.services.socket_manager.threading.Thread')
    def test_telemetry_handling(self, mock_thread):
        from dashboard.services.socket_manager import SocketManager
        SocketManager._instance = None
        manager = SocketManager()

        data = {"tick": 1, "integrity": {}}
        manager.telemetry_queue.put(data)

        result = manager.get_latest_telemetry()
        self.assertEqual(result, data)
        self.assertTrue(manager.telemetry_queue.empty())

    @patch('dashboard.services.socket_manager.threading.Thread')
    def test_audit_logs(self, mock_thread):
        from dashboard.services.socket_manager import SocketManager
        SocketManager._instance = None
        manager = SocketManager()

        log1 = {"command_id": "1"}
        log2 = {"command_id": "2"}
        manager.audit_log_queue.put(log1)
        manager.audit_log_queue.put(log2)

        logs = manager.get_audit_logs()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0], log1)
        self.assertEqual(logs[1], log2)
        self.assertTrue(manager.audit_log_queue.empty())
