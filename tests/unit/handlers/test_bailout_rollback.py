import pytest
from unittest.mock import MagicMock
from modules.finance.handlers.bailout import BailoutHandler
from modules.system.api import AssetBuyoutRequestDTO, AssetBuyoutResultDTO

def test_bailout_rollback_success():
    asset_system = MagicMock()
    handler = BailoutHandler(asset_system)

    request = AssetBuyoutRequestDTO(seller_id=1, inventory={"A": 10}, market_prices={"A": 100})

    result = AssetBuyoutResultDTO(success=True, total_paid_pennies=1000, items_acquired={"A": 10}, buyer_id=2, transaction_id="test_bailout")

    asset_system.execute_asset_buyout.return_value = result
    asset_system.rollback_asset_buyout.return_value = True

    # Execute
    res = handler.execute(request, None)
    assert res.success is True

    # Verify rollback
    assert handler.rollback("test_bailout", None) is True
    asset_system.rollback_asset_buyout.assert_called_once_with(result)
