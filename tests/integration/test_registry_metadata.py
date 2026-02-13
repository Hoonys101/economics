import pytest
from modules.system.registry import GlobalRegistry
from modules.system.services.schema_loader import SchemaLoader
from simulation.dtos.registry_dtos import ParameterSchemaDTO

class TestRegistryMetadata:

    def test_schema_loader_loads_data(self):
        """Verify SchemaLoader can read and parse the default schema file."""
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
        registry = GlobalRegistry()
        # Access private member for verification (or use public getter if available)
        # We implemented get_metadata, so use that.

        # Pick a known key from registry_schema.yaml
        # Based on previous read_file, "government.corporate_tax_rate" exists.
        known_key = "government.corporate_tax_rate"

        metadata = registry.get_metadata(known_key)
        assert metadata is not None
        assert metadata["key"] == known_key
        assert metadata["label"] == "Corporate Tax Rate"
        assert metadata["data_type"] == "float"

    def test_global_registry_get_metadata_returns_none_for_unknown_key(self):
        """Verify get_metadata returns None for non-existent keys."""
        registry = GlobalRegistry()
        metadata = registry.get_metadata("non.existent.key")
        assert metadata is None

    def test_global_registry_get_entry_returns_none_for_unset_key(self):
        """Verify get_entry returns None if key is not set."""
        registry = GlobalRegistry()
        entry = registry.get_entry("some.key")
        assert entry is None

    def test_global_registry_get_entry_returns_entry(self):
        """Verify get_entry returns the RegistryEntry after setting a value."""
        registry = GlobalRegistry()
        key = "test.param"
        registry.set(key, 123)

        entry = registry.get_entry(key)
        assert entry is not None
        assert entry.value == 123
        assert entry.is_locked is False
