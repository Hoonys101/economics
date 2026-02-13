import unittest
from dashboard.services.registry_service import RegistryService, RegistryMetadata

class TestRegistryService(unittest.TestCase):
    def test_get_all_metadata(self):
        service = RegistryService()
        metadata = service.get_all_metadata()
        self.assertIsInstance(metadata, list)
        self.assertTrue(len(metadata) > 0)
        self.assertIsInstance(metadata[0], RegistryMetadata)

    def test_get_metadata_by_key(self):
        service = RegistryService()
        # "corporate_tax_rate" is a known key in our shim
        meta = service.get_metadata("corporate_tax_rate")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.key, "corporate_tax_rate")

    def test_get_metadata_unknown_key(self):
        service = RegistryService()
        meta = service.get_metadata("unknown_key_xyz")
        self.assertIsNone(meta)
