import pytest
from unittest.mock import MagicMock, create_autospec, PropertyMock
from modules.common.services.public_service import PublicSimulationService
from modules.common.api import (
    ISimulationRepository, IEventBroker, IMetricsProvider, IndicatorSubscriptionDTO,
    AgentNotFoundError, ProtocolViolationError, IFirm, IHousehold
)

class TestPublicSimulationService:

    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=ISimulationRepository)

    @pytest.fixture
    def mock_metrics(self):
        return MagicMock(spec=IMetricsProvider)

    @pytest.fixture
    def mock_broker(self):
        return MagicMock(spec=IEventBroker)

    @pytest.fixture
    def service(self, mock_repo, mock_metrics, mock_broker):
        return PublicSimulationService(mock_repo, mock_metrics, mock_broker)

    def test_get_firm_status_success(self, service, mock_repo):
        # Setup
        firm_id = "101"
        mock_firm = MagicMock(spec=IFirm)
        # Use PropertyMock for protocol properties
        type(mock_firm).id = PropertyMock(return_value=101)
        type(mock_firm).capital = PropertyMock(return_value=5000.0)
        type(mock_firm).capital_stock = PropertyMock(return_value=5000.0)
        type(mock_firm).inventory = PropertyMock(return_value={})

        # Configure methods
        mock_firm.get_all_items.return_value = {"item1": 10, "item2": 5}

        mock_repo.get_agent.return_value = mock_firm

        # Execute
        result = service.get_firm_status(firm_id)

        # Verify
        mock_repo.get_agent.assert_called_with(101) # Check int casting
        assert result.firm_id == "101"
        assert result.capital == 5000.0
        assert result.inventory_count == 15

    def test_get_firm_status_not_found(self, service, mock_repo):
        mock_repo.get_agent.return_value = None

        with pytest.raises(AgentNotFoundError):
            service.get_firm_status("999")

    def test_get_firm_status_protocol_violation_isinstance(self, service, mock_repo):
        # Case 1: Object fails isinstance check (e.g. completely different type)
        class NotAFirm:
            pass

        mock_repo.get_agent.return_value = NotAFirm()

        with pytest.raises(ProtocolViolationError):
            service.get_firm_status("101")

    def test_get_firm_status_protocol_integrity_missing_attr(self, service, mock_repo):
        # Case 2: Object passes isinstance (mock) but misses attributes required by Mapper
        # This simulates the "Leaky Boundary" where Service passes but Mapper catches it.

        # Create a mock that satisfies IFirm for isinstance (due to spec)
        # but DELETE the attributes at runtime to trigger Mapper's firewall.
        mock_firm = MagicMock(spec=IFirm)

        # Ensure it passes isinstance check in Service
        # (MagicMock(spec=IFirm) usually passes strict isinstance if attributes exist)

        # But we want to fail inside Mapper.
        # So we delete 'capital_stock' from the instance.
        del mock_firm.capital_stock
        # Also ensure id is present so it doesn't fail there first
        type(mock_firm).id = PropertyMock(return_value=101)

        mock_repo.get_agent.return_value = mock_firm

        # The Service calls isinstance(agent, IFirm).
        # If this passes, Mapper is called.
        # Mapper checks hasattr(agent, 'capital_stock').
        # This should raise ProtocolViolationError.

        # Note: If isinstance fails first, we get ProtocolViolationError from Service.
        # If isinstance passes, we get ProtocolViolationError from Mapper.
        # Either way, we want ProtocolViolationError.

        with pytest.raises(ProtocolViolationError):
            service.get_firm_status("101")

    def test_subscribe_to_indicators_success(self, service, mock_broker):
        # Setup
        callback = MagicMock()
        dto = IndicatorSubscriptionDTO(
            subscriber_id="test_sub",
            indicator_keys=["gdp", "cpi"],
            callback=callback
        )

        # Execute
        result = service.subscribe_to_indicators(dto)

        # Verify
        assert result is True
        mock_broker.subscribe.assert_called_once()
        args, _ = mock_broker.subscribe.call_args
        assert args[0] == "economic_indicators"

        # Simulate Event
        handler = args[1]
        test_data = {"gdp": 100.0, "cpi": 2.0, "ignore_me": 5.0}
        handler(test_data)

        # Check Callback filtered
        callback.assert_called_once_with({"gdp": 100.0, "cpi": 2.0})

    def test_subscribe_no_broker(self, mock_repo):
        # Service without broker
        service = PublicSimulationService(mock_repo, None, None)
        dto = IndicatorSubscriptionDTO("id", [], lambda x: None)

        assert service.subscribe_to_indicators(dto) is False

    def test_get_global_indicators(self, service, mock_metrics):
        # Setup
        mock_dto = MagicMock()
        mock_dto.gdp = 1000.0
        mock_dto.cpi = 2.5
        mock_dto.unemployment_rate = 0.05
        mock_metrics.get_economic_indicators.return_value = mock_dto

        # Execute
        result = service.get_global_indicators()

        # Verify
        assert result.gdp == 1000.0
        assert result.cpi == 2.5
        assert result.unemployment_rate == 0.05
        mock_metrics.get_economic_indicators.assert_called_once()
