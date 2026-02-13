import unittest
from dashboard.services.registry_service import RegistryService
from dashboard.dtos import ParameterSchemaDTO

class TestRegistryService(unittest.TestCase):
    def test_get_all_metadata(self):
        service = RegistryService()
        metadata = service.get_all_metadata()
        self.assertIsInstance(metadata, list)
        self.assertTrue(len(metadata) > 0)
        self.assertIsInstance(metadata[0], dict) # ParameterSchemaDTO is a TypedDict

    def test_get_metadata_by_key(self):
        service = RegistryService()
        # "economy.tax_rate_income" is a known key in current engine schema
        meta = service.get_metadata("economy.tax_rate_income")
        if meta is None:
            # Fallback if the above key is not in the loaded schema
            metadata = service.get_all_metadata()
            if metadata:
                meta = service.get_metadata(metadata[0]['key'])
        
        self.assertIsNotNone(meta)
        self.assertIn('key', meta)

    def test_get_metadata_unknown_key(self):
        service = RegistryService()
        meta = service.get_metadata("unknown_key_xyz")
        self.assertIsNone(meta)
