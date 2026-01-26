# tests/test_logger.py
import os
from pathlib import Path
import csv
import unittest
import sys
import logging

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from utils.logger import Logger


class TestLogger(unittest.TestCase):
    def setUp(self):
        """Set up for test cases, ensuring complete isolation."""
        # Completely reset the singleton instance to ensure isolation
        Logger._instance = None
        Logger._initialized = False

        self.log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        self.logger = Logger(log_dir=self.log_dir)
        # Clear any logs from previous runs
        self.logger.clear_logs()

    def tearDown(self):
        """Tear down after test cases, ensuring complete cleanup."""
        # Close all handlers and clear logs
        self.logger.clear_logs()
        # Reset the singleton instance after the test
        Logger._instance = None
        Logger._initialized = False

    def test_singleton_instance(self):
        """Test if the logger is a singleton."""
        logger2 = Logger()
        self.assertIs(self.logger, logger2)

    def test_log_writing(self):
        """Test if a standard log message is written correctly."""
        log_type = "TestLog"
        self.logger.log(
            logging.INFO,
            "This is a test message.",
            log_type=log_type,
            tick=1,
            agent_type="TestAgent",
            agent_id=101,
            method_name="test_method",
            test_data="value",
        )

        log_file_path = os.path.join(
            self.logger.log_dir, f"simulation_log_{log_type}.csv"
        )
        self.assertTrue(os.path.exists(log_file_path))

        with open(log_file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(
                header,
                [
                    "timestamp",
                    "tick",
                    "agent_type",
                    "agent_id",
                    "method_name",
                    "message",
                    "test_data",
                ],
            )

            log_data = next(reader)
            # We don't check the timestamp as it's dynamic
            self.assertEqual(
                log_data[1:],
                [
                    "1",
                    "TestAgent",
                    "101",
                    "test_method",
                    "This is a test message.",
                    "value",
                ],
            )

    def test_clear_logs(self):
        """Test if the log file is cleared properly."""
        log_type = "ClearTestLog"
        self.logger.log(
            logging.INFO,
            "message",
            log_type=log_type,
            tick=1,
            agent_type="Agent",
            agent_id=1,
            method_name="method",
        )
        self.logger.clear_logs()

        log_file_path = os.path.join(
            self.logger.log_dir, f"simulation_log_{log_type}.csv"
        )
        self.assertFalse(
            os.path.exists(log_file_path)
        )  # File should be removed after clear_logs


if __name__ == "__main__":
    unittest.main()
