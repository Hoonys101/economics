import unittest
from unittest.mock import patch, mock_open
from modules.system.services.schema_loader import SchemaLoader
import logging
import yaml

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestSchemaLoader(unittest.TestCase):
    @patch('modules.system.services.schema_loader.yaml.safe_load')
    def test_load_schema_success(self, mock_yaml_load):
        mock_data = [{
            'key': 'test.param',
            'label': 'Test Param',
            'description': 'A test parameter',
            'widget_type': 'slider',
            'data_type': 'float',
            'min_value': 0.0,
            'max_value': 1.0,
            'step': 0.1,
            'category': 'Test'
        }]
        mock_yaml_load.return_value = mock_data

        with patch("builtins.open", mock_open(read_data="content")):
            schema = SchemaLoader.load_schema("dummy.yaml")
            self.assertEqual(len(schema), 1)
            self.assertEqual(schema[0]['key'], "test.param")

    def test_load_schema_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            schema = SchemaLoader.load_schema("nonexistent.yaml")
            self.assertEqual(schema, [])

    @patch('modules.system.services.schema_loader.yaml.safe_load')
    def test_load_schema_invalid_structure(self, mock_yaml_load):
        # Returns dict instead of list
        mock_yaml_load.return_value = {"key": "val"}

        with patch("builtins.open", mock_open(read_data="content")):
            schema = SchemaLoader.load_schema("invalid.yaml")
            self.assertEqual(schema, [])

    @patch('modules.system.services.schema_loader.yaml.safe_load')
    def test_load_schema_yaml_error(self, mock_yaml_load):
        mock_yaml_load.side_effect = yaml.YAMLError("parse error")

        with patch("builtins.open", mock_open(read_data="invalid")):
            schema = SchemaLoader.load_schema("invalid.yaml")
            self.assertEqual(schema, [])
