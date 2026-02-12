import unittest
from unittest.mock import patch, MagicMock
import os
from modules.common.protocol import enforce_purity, ProtocolViolationError, IS_PURITY_CHECK_ENABLED

class TestProtocolShield(unittest.TestCase):

    def setUp(self):
        # By default, tests run with ENABLE_PURITY_CHECKS=false (unless set in env)
        # We will patch the variable in tests.
        pass

    @patch("modules.common.protocol.IS_PURITY_CHECK_ENABLED", True)
    @patch("inspect.stack")
    def test_authorized_call(self, mock_stack):
        # Mock caller stack frame
        mock_frame = MagicMock()
        # Simulate call from authorized module (e.g., modules/finance/some_file.py)
        mock_frame.filename = "/app/modules/finance/some_file.py"
        mock_stack.return_value = [MagicMock(), mock_frame]

        @enforce_purity(allowed_modules=["modules/finance/"])
        def protected_function():
            return "success"

        result = protected_function()
        self.assertEqual(result, "success")

    @patch("modules.common.protocol.IS_PURITY_CHECK_ENABLED", True)
    @patch("inspect.stack")
    def test_unauthorized_call(self, mock_stack):
        # Mock caller stack frame
        mock_frame = MagicMock()
        # Simulate call from unauthorized module (e.g., scripts/random_script.py)
        mock_frame.filename = "/app/scripts/random_script.py"
        mock_stack.return_value = [MagicMock(), mock_frame]

        @enforce_purity(allowed_modules=["modules/finance/"])
        def protected_function():
            return "success"

        with self.assertRaises(ProtocolViolationError):
            protected_function()

    @patch("modules.common.protocol.IS_PURITY_CHECK_ENABLED", False)
    @patch("inspect.stack")
    def test_disabled_shield(self, mock_stack):
        # Mock caller stack frame
        mock_frame = MagicMock()
        # Simulate call from unauthorized module, but shield is disabled
        mock_frame.filename = "/app/scripts/random_script.py"
        mock_stack.return_value = [MagicMock(), mock_frame]

        @enforce_purity(allowed_modules=["modules/finance/"])
        def protected_function():
            return "success"

        # Should pass because shield is disabled
        result = protected_function()
        self.assertEqual(result, "success")

if __name__ == "__main__":
    unittest.main()
