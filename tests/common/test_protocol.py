import unittest
from unittest.mock import patch, MagicMock
import os
from modules.common.protocol import enforce_purity, ProtocolViolationError, IS_PURITY_CHECK_ENABLED

# Define a named tuple to mimic inspect.FrameInfo or the tuple structure
# FrameInfo = namedtuple('FrameInfo', ['frame', 'filename', 'lineno', 'function', 'code_context', 'index'])
# Simplified mock object approach is also fine if attributes are accessible.

class TestProtocolShield(unittest.TestCase):

    def setUp(self):
        pass

    @patch("modules.common.protocol.IS_PURITY_CHECK_ENABLED", True)
    @patch("inspect.stack")
    def test_authorized_call(self, mock_stack):
        # Mock caller stack frame
        mock_frame = MagicMock()
        # Use an absolute path that contains the allowed module path
        # We simulate the caller being in 'modules/finance/some_file.py'
        # The check logic: "modules/finance" in "/app/modules/finance/some_file.py"
        mock_frame.filename = "/app/modules/finance/some_file.py"

        # Stack[0] is current frame, Stack[1] is caller
        mock_stack.return_value = [MagicMock(), mock_frame]

        @enforce_purity(allowed_modules=["modules/finance/"])
        def protected_function():
            return "success"

        result = protected_function()
        self.assertEqual(result, "success")

    @patch("modules.common.protocol.IS_PURITY_CHECK_ENABLED", True)
    @patch("inspect.stack")
    def test_unauthorized_call(self, mock_stack):
        mock_frame = MagicMock()
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
        mock_frame = MagicMock()
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
