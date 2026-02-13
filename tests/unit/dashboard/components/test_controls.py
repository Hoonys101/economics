import unittest
from unittest.mock import MagicMock, patch
from dashboard.components.controls import render_dynamic_controls
from dashboard.dtos import ParameterSchemaDTO
from simulation.dtos.commands import GodCommandDTO

class TestControls(unittest.TestCase):
    def setUp(self):
        self.mock_st = MagicMock()
        self.mock_registry_service = MagicMock()

        # Patch modules
        self.st_patcher = patch("dashboard.components.controls.st", self.mock_st)
        self.registry_patcher = patch("dashboard.components.controls.RegistryService", return_value=self.mock_registry_service)

        self.mock_st_module = self.st_patcher.start()
        self.mock_registry_service_cls = self.registry_patcher.start()

        # Setup session state
        self.mock_st.session_state = {}

        # Configure st.columns to return a list of mocks
        self.mock_st.columns.return_value = [MagicMock(), MagicMock()]

    def tearDown(self):
        self.st_patcher.stop()
        self.registry_patcher.stop()

    def test_render_dynamic_controls_tabs(self):
        # Mock Schema with unit
        schema = [
            ParameterSchemaDTO(
                key="gov.tax", label="Tax", description="Tax Rate",
                widget_type="slider", data_type="float",
                min_value=0.0, max_value=1.0, step=0.1, category="Fiscal", options=None, unit="%"
            )
        ]
        self.mock_registry_service.get_all_metadata.return_value = schema

        # Mock Telemetry
        self.mock_st.session_state = {
            "telemetry_buffer": {"registry": {"gov.tax": 0.5}}
        }

        # Call function
        render_dynamic_controls(use_tabs=True)

        # Verify tabs created
        self.mock_st.tabs.assert_called()
        args, _ = self.mock_st.tabs.call_args
        self.assertIn("🏛️ Fiscal", args[0])

        # Verify slider created with unit in label
        self.mock_st.slider.assert_called()
        _, kwargs = self.mock_st.slider.call_args
        self.assertIn("Tax [%]", kwargs['label']) # Adjusted for implementation
        self.assertEqual(kwargs['min_value'], 0.0)
        self.assertEqual(kwargs['key'], "ui_gov.tax")

    def test_on_change_generates_command(self):
        # ... setup schema ...
        schema = [
            ParameterSchemaDTO(
                key="gov.tax", label="Tax", description="Desc",
                widget_type="slider", data_type="float",
                min_value=0.0, max_value=1.0, step=0.1, category="Fiscal", options=None, unit="%"
            )
        ]
        self.mock_registry_service.get_all_metadata.return_value = schema

        self.mock_st.session_state = {
            "telemetry_buffer": {"registry": {"gov.tax": 0.8}},
            "ui_gov.tax": 0.8,
            "pending_commands": []
        }

        # Render to register callback
        render_dynamic_controls()

        # Extract callback
        _, kwargs = self.mock_st.slider.call_args
        on_change = kwargs['on_change']

        # Simulate interaction
        on_change()

        # Verify command
        pending = self.mock_st.session_state["pending_commands"]
        self.assertEqual(len(pending), 1)
        cmd = pending[0]
        self.assertIsInstance(cmd, GodCommandDTO)
        self.assertEqual(cmd.parameter_key, "gov.tax")
        self.assertEqual(cmd.new_value, 0.8)

    def test_missing_registry_value_disables_widget(self):
        # Schema for key that is missing in telemetry
        schema = [
            ParameterSchemaDTO(
                key="missing.key", label="Ghost Param", description="Desc",
                widget_type="slider", data_type="float",
                min_value=0.0, max_value=1.0, step=0.1, category="Fiscal", options=None, unit=""
            )
        ]
        self.mock_registry_service.get_all_metadata.return_value = schema

        # Empty telemetry
        self.mock_st.session_state = {
            "telemetry_buffer": {"registry": {}},
            "god_mode_active": True # Enable god mode, but widget should still be disabled/warned
        }

        render_dynamic_controls()

        self.mock_st.slider.assert_called()
        _, kwargs = self.mock_st.slider.call_args

        # Check label warning
        self.assertIn("Ghost Param (⚠️ N/A)", kwargs['label'])

        # Check disabled state (True because it is missing)
        self.assertTrue(kwargs['disabled'])
