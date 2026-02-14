import pytest
from unittest.mock import Mock, MagicMock, create_autospec
from modules.household.connectors.housing_connector import HousingConnector, IHousingSystem
from modules.household.api import HousingActionDTO

class TestHousingConnector:
    def test_initiate_purchase(self):
        connector = HousingConnector()
        # Use create_autospec so isinstance(system, IHousingSystem) returns True
        system = create_autospec(IHousingSystem, instance=True)

        action = HousingActionDTO(
            action_type="INITIATE_PURCHASE",
            property_id=1,
            offer_price=1000,
            down_payment_amount=200
        )

        connector.execute_action(action, system, 1)

        expected_dict = {
            "decision_type": "INITIATE_PURCHASE",
            "target_property_id": 1,
            "offer_price": 1000,
            "down_payment_amount": 200
        }
        system.initiate_purchase.assert_called_with(expected_dict, buyer_id=1)

    def test_unknown_action(self):
        connector = HousingConnector()
        system = Mock()

        action = HousingActionDTO(
            action_type="UNKNOWN",
            property_id=1
        )

        connector.execute_action(action, system, 1)
        system.initiate_purchase.assert_not_called()
