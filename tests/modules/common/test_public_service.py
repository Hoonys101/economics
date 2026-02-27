import pytest
from unittest.mock import MagicMock, create_autospec
from modules.common.services.public_service import PublicSimulationService
from modules.common.api import (
    ISimulationRepository, IEventBroker, IndicatorSubscriptionDTO,
    AgentNotFoundError, ProtocolViolationError, IFirm, IHousehold
)

class TestPublicSimulationService:

    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=ISimulationRepository)

    @pytest.fixture
    def mock_broker(self):
        return MagicMock(spec=IEventBroker)

    @pytest.fixture
    def service(self, mock_repo, mock_broker):
        return PublicSimulationService(mock_repo, mock_broker)

    def test_get_firm_status_success(self, service, mock_repo):
        # Setup
        firm_id = "101"
        mock_firm = MagicMock(spec=IFirm)
        mock_firm.id = 101
        # Set attributes required by FirmMapper
        mock_firm.capital_stock = 5000.0 # Used by Mapper
        mock_firm.capital = 5000.0 # Used by Protocol check (if checked)
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

    def test_get_firm_status_protocol_violation(self, service, mock_repo):
        # Return an agent that is NOT a firm

        # Using a class that lacks required attributes
        class NotAFirm:
            id = 101
            # Missing capital, inventory

        mock_repo.get_agent.return_value = NotAFirm()

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
        service = PublicSimulationService(mock_repo, None)
        dto = IndicatorSubscriptionDTO("id", [], lambda x: None)

        assert service.subscribe_to_indicators(dto) is False
