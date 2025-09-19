# tests/test_logger.py
import os
import csv
import unittest
import sys
import logging

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import Logger

class TestLogger(unittest.TestCase):

    def setUp(self):
        """Set up for test cases."""
        self.log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        self.logger = Logger(log_dir=self.log_dir)
        # Ensure the log files are clean before each test
        self.logger.clear_logs()

    def tearDown(self):
        """Tear down after test cases."""
        self.logger.close() # Close the file handle before trying to remove the file
        # Clean up the log files after tests
        self.logger.clear_logs()

    def test_singleton_instance(self):
        """Test if the logger is a singleton."""
        logger2 = Logger()
        self.assertIs(self.logger, logger2)

    def test_log_writing(self):
        """Test if a standard log message is written correctly."""
        log_type = "TestLog"
        self.logger.log(logging.INFO, log_type, 1, "TestAgent", 101, "test_method", "This is a test message.", extra={'test_data': 'value'})
        self.logger.close() # Close the handle so we can read the file

        log_file_path = os.path.join(self.logger.log_dir, f"simulation_log_{log_type}.csv")
        self.assertTrue(os.path.exists(log_file_path))

        with open(log_file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["timestamp", "tick", "agent_type", "agent_id", "method_name", "message", "test_data"])
            
            log_data = next(reader)
            # We don't check the timestamp as it's dynamic
            self.assertEqual(log_data[1:], ['1', 'TestAgent', '101', 'test_method', 'This is a test message.', 'value'])

    def test_clear_logs(self):
        """Test if the log file is cleared properly."""
        log_type = "ClearTestLog"
        self.logger.log(logging.INFO, log_type, 1, "Agent", 1, "method", "message")
        self.logger.clear_logs() # This already closes the file handle

        log_file_path = os.path.join(self.logger.log_dir, f"simulation_log_{log_type}.csv")
        self.assertFalse(os.path.exists(log_file_path)) # File should be removed after clear_logs

if __name__ == '__main__':
    unittest.main()
