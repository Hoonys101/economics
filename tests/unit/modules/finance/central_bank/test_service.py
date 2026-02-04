import pytest
from unittest.mock import MagicMock
from modules.finance.central_bank.service import CentralBankService
from modules.finance.central_bank.api import InvalidPolicyRateError, TreasuryServiceError
from modules.government.treasury.api import ITreasuryService, TreasuryOperationResultDTO
from modules.system.constants import ID_CENTRAL_BANK

@pytest.fixture
def mock_treasury_service():
    return MagicMock(spec=ITreasuryService)

@pytest.fixture
def central_bank_service():
    return CentralBankService(tick_provider=lambda: 100)

def test_set_policy_rate_valid(central_bank_service):
    dto = central_bank_service.set_policy_rate(0.03)
    assert dto["rate"] == 0.03
    assert dto["decision_tick"] == 100
    assert dto["effective_tick"] == 101

    # Check if get returns the same
    current = central_bank_service.get_policy_rate()
    assert current["rate"] == 0.03

def test_set_policy_rate_invalid(central_bank_service):
    with pytest.raises(InvalidPolicyRateError):
        central_bank_service.set_policy_rate(-0.01)

def test_conduct_omo_purchase_success(central_bank_service, mock_treasury_service):
    # Setup mock
    mock_result: TreasuryOperationResultDTO = {
        "success": True,
        "bonds_exchanged": 10,
        "cash_exchanged": 1000.0,
        "message": "Success"
    }
    mock_treasury_service.execute_market_purchase.return_value = mock_result

    result = central_bank_service.conduct_open_market_operation(
        mock_treasury_service, "purchase", 1000.0, currency="USD"
    )

    assert result["success"]
    assert result["operation_type"] == "purchase"
    assert result["bonds_transacted_count"] == 10
    assert result["cash_transferred"] == 1000.0

    mock_treasury_service.execute_market_purchase.assert_called_with(
        buyer_id=ID_CENTRAL_BANK,
        target_cash_amount=1000.0,
        currency="USD"
    )

def test_conduct_omo_sale_success(central_bank_service, mock_treasury_service):
    mock_result: TreasuryOperationResultDTO = {
        "success": True,
        "bonds_exchanged": 5,
        "cash_exchanged": 500.0,
        "message": "Sold"
    }
    mock_treasury_service.execute_market_sale.return_value = mock_result

    result = central_bank_service.conduct_open_market_operation(
        mock_treasury_service, "sale", 500.0, currency="EUR"
    )

    assert result["success"]
    assert result["operation_type"] == "sale"
    assert result["cash_transferred"] == 500.0

    mock_treasury_service.execute_market_sale.assert_called_with(
        seller_id=ID_CENTRAL_BANK,
        target_cash_amount=500.0,
        currency="EUR"
    )

def test_conduct_omo_failure(central_bank_service, mock_treasury_service):
    mock_result: TreasuryOperationResultDTO = {
        "success": False,
        "bonds_exchanged": 0,
        "cash_exchanged": 0.0,
        "message": "Not enough bonds"
    }
    mock_treasury_service.execute_market_purchase.return_value = mock_result

    with pytest.raises(TreasuryServiceError) as exc:
        central_bank_service.conduct_open_market_operation(
            mock_treasury_service, "purchase", 1000.0
        )
    assert "Not enough bonds" in str(exc.value)
