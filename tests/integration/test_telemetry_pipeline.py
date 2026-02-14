import pytest
from unittest.mock import MagicMock
from modules.system.registry import GlobalRegistry
from modules.system.telemetry import TelemetryCollector
from modules.system.services.command_service import CommandService
from simulation.dtos.commands import GodCommandDTO
from modules.system.api import OriginType

class TestTelemetryPipeline:

    @pytest.fixture
    def registry(self):
        return GlobalRegistry()

    @pytest.fixture
    def telemetry_collector(self, registry):
        return TelemetryCollector(registry)

    @pytest.fixture
    def command_service(self, registry, telemetry_collector):
        # Setup registry
        registry.set("system.telemetry_collector", telemetry_collector, origin=OriginType.SYSTEM)

        # Mock dependencies for CommandService
        mock_settlement = MagicMock()
        mock_agent_registry = MagicMock()

        return CommandService(registry, mock_settlement, mock_agent_registry)

    def test_update_telemetry_command_updates_subscriptions(self, command_service, telemetry_collector, registry):
        # Arrange
        # Setup some data in registry to be collected
        # TelemetryCollector splits by dot. root is "econ", sub is "gdp".
        registry.set("econ", {"gdp": 1000}, origin=OriginType.SYSTEM)
        registry.set("pop", {"count": 50}, origin=OriginType.SYSTEM)

        mask = ["econ.gdp", "pop.count"]
        cmd = GodCommandDTO(
            command_type="UPDATE_TELEMETRY",
            target_domain="System",
            parameter_key="telemetry_mask",
            new_value=mask
        )

        # Act
        command_service.execute_command_batch([cmd], tick=1, baseline_m2=0)

        # Assert
        # Check subscriptions
        assert "econ.gdp" in telemetry_collector._subscriptions
        assert "pop.count" in telemetry_collector._subscriptions
        assert len(telemetry_collector._subscriptions) == 2

        # Verify harvest
        snapshot = telemetry_collector.harvest(current_tick=1)
        assert snapshot.data["econ.gdp"] == 1000
        assert snapshot.data["pop.count"] == 50

    def test_update_telemetry_command_replaces_subscriptions(self, command_service, telemetry_collector, registry):
        # Arrange
        # Initial subscription
        # Setup old metric structure
        registry.set("old", {"metric": 999}, origin=OriginType.SYSTEM)
        telemetry_collector.subscribe(["old.metric"], frequency_interval=1)

        mask = ["new.metric"]
        cmd = GodCommandDTO(
            command_type="UPDATE_TELEMETRY",
            target_domain="System",
            parameter_key="telemetry_mask",
            new_value=mask
        )
        registry.set("new", {"metric": 123}, origin=OriginType.SYSTEM)

        # Act
        command_service.execute_command_batch([cmd], tick=1, baseline_m2=0)

        # Assert
        assert "old.metric" not in telemetry_collector._subscriptions
        assert "new.metric" in telemetry_collector._subscriptions

        snapshot = telemetry_collector.harvest(current_tick=1)
        assert snapshot.data["new.metric"] == 123

    def test_update_telemetry_invalid_value_type(self, command_service):
        # Arrange
        cmd = GodCommandDTO(
            command_type="UPDATE_TELEMETRY",
            target_domain="System",
            parameter_key="telemetry_mask",
            new_value="invalid_string_not_list"
        )

        # Act & Assert
        # CommandService catches exceptions and returns failure response
        results = command_service.execute_command_batch([cmd], tick=1, baseline_m2=0)

        assert len(results) == 1
        assert results[0].success is False
        assert "must be a list" in results[0].failure_reason
