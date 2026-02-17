import unittest
from unittest.mock import patch
from dashboard.services.registry_service import RegistryService
from dashboard.dtos import ParameterSchemaDTO

class TestRegistryService(unittest.TestCase):
    def test_get_all_metadata(self):
        mock_data = [
            {"key": "test", "label": "Test", "widget_type": "text", "description": "Desc", "data_type": "string", "category": "Test", "unit": ""}
        ]
        with patch('yaml.safe_load', return_value=mock_data):
            service = RegistryService()
            metadata = service.get_all_metadata()
            self.assertIsInstance(metadata, list)
            self.assertTrue(len(metadata) > 0)
            self.assertIsInstance(metadata[0], dict) # ParameterSchemaDTO is a TypedDict

    def test_get_metadata_by_key(self):
        # "economy.tax_rate_income" is a known key in current engine schema
        key = "economy.tax_rate_income"
        mock_data = [
            {"key": key, "label": "Income Tax Rate", "widget_type": "slider", "description": "Desc", "data_type": "float", "category": "Test", "unit": "%"}
        ]
        with patch('yaml.safe_load', return_value=mock_data):
            service = RegistryService()

            meta = service.get_metadata(key)
            if meta is None:
                # Fallback if the above key is not in the loaded schema
                metadata = service.get_all_metadata()
                if metadata:
                    meta = service.get_metadata(metadata[0]['key'])

            self.assertIsNotNone(meta)
            self.assertIn('key', meta)
            self.assertEqual(meta['key'], key)

    def test_get_metadata_unknown_key(self):
        with patch('yaml.safe_load', return_value=[]):
            service = RegistryService()
            meta = service.get_metadata("unknown_key_xyz")
            self.assertIsNone(meta)
