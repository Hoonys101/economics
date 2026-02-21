import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.handlers.bailout import BailoutHandler
from modules.system.api import AssetBuyoutRequestDTO, IAssetRecoverySystem, AssetBuyoutResultDTO

def test_bailout_handler_validate_success():
    handler = BailoutHandler(Mock(spec=IAssetRecoverySystem))
    request = AssetBuyoutRequestDTO(
        seller_id=1,
        inventory={},
        market_prices={},
        distress_discount=0.5
    )
    assert handler.validate(request, None) is True

def test_bailout_handler_validate_fail_type():
    handler = BailoutHandler(Mock(spec=IAssetRecoverySystem))
    assert handler.validate("invalid", None) is False

def test_bailout_handler_execute_success():
    mock_system = Mock(spec=IAssetRecoverySystem)
    expected_result = AssetBuyoutResultDTO(True, 100, {}, 1, "tx1")
    mock_system.execute_asset_buyout.return_value = expected_result

    handler = BailoutHandler(mock_system)
    request = AssetBuyoutRequestDTO(1, {}, {}, 0.5)

    result = handler.execute(request, None)

    assert result == expected_result
    mock_system.execute_asset_buyout.assert_called_with(request)
