import pytest
from unittest.mock import patch
from modules.system.registry import GlobalRegistry
from modules.system.services.schema_loader import SchemaLoader
from simulation.dtos.registry_dtos import ParameterSchemaDTO

class TestRegistryMetadata:

    def test_schema_loader_loads_data(self):
        """Verify SchemaLoader can read and parse the default schema file."""
        mock_data = [
            {"key": "test", "label": "Test", "widget_type": "text", "description": "Desc", "data_type": "string", "category": "Test", "unit": ""}
        ]
        with patch('yaml.safe_load', return_value=mock_data):
            schemas = SchemaLoader.load_schema()
            assert isinstance(schemas, list)
            assert len(schemas) > 0

            # Check basic structure of the first item
            first_item = schemas[0]
            assert "key" in first_item
            assert "label" in first_item
            assert "widget_type" in first_item

    def test_global_registry_loads_metadata_on_init(self):
        """Verify GlobalRegistry loads metadata during initialization."""
        known_key = "government.corporate_tax_rate"
        mock_data = [
            {
                "key": known_key,
                "label": "Corporate Tax Rate",
                "description": "The tax rate applied to corporate profits.",
                "widget_type": "slider",
                "data_type": "float",
                "min_value": 0.0,
                "max_value": 0.5,
                "step": 0.01,
                "category": "Fiscal",
                "unit": "%"
            }
        ]

        with patch('yaml.safe_load', return_value=mock_data):
            registry = GlobalRegistry()
            # Access private member for verification (or use public getter if available)
            # We implemented get_metadata, so use that.

            metadata = registry.get_metadata(known_key)
            assert metadata is not None
            assert metadata["key"] == known_key
            assert metadata["label"] == "Corporate Tax Rate"
            assert metadata["data_type"] == "float"

    def test_global_registry_get_metadata_returns_none_for_unknown_key(self):
        """Verify get_metadata returns None for non-existent keys."""
        # Ensure we don't crash on init if yaml is mocked empty by default in conftest
        # But patching here explicitly is safer
        with patch('yaml.safe_load', return_value=[]):
            registry = GlobalRegistry()
            metadata = registry.get_metadata("non.existent.key")
            assert metadata is None

    def test_global_registry_get_entry_returns_none_for_unset_key(self):
        """Verify get_entry returns None if key is not set."""
        with patch('yaml.safe_load', return_value=[]):
            registry = GlobalRegistry()
            entry = registry.get_entry("some.key")
            assert entry is None

    def test_global_registry_get_entry_returns_entry(self):
        """Verify get_entry returns the RegistryEntry after setting a value."""
        with patch('yaml.safe_load', return_value=[]):
            registry = GlobalRegistry()
            key = "test.param"
            registry.set(key, 123)

            entry = registry.get_entry(key)
            assert entry is not None
            assert entry.value == 123
            assert entry.is_locked is False
