import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from modules.finance.api import TaxCollectionResult

class TestGovernmentTax:
    @pytest.fixture
    def government(self):
        config = MagicMock()
        # Mocking config attributes accessed in __init__
        config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        config.INCOME_TAX_RATE = 0.1
        config.CORPORATE_TAX_RATE = 0.2
        config.TICKS_PER_YEAR = 100
        config.TAX_BRACKETS = [] # Add this to avoid error in TaxAgency init if it checks

        gov = Government(id=1, initial_assets=1000.0, config_module=config)
        gov.tax_agency = MagicMock()
        gov.settlement_system = MagicMock()
        return gov

    def test_record_revenue_success(self, government):
        # Arrange
        result: TaxCollectionResult = {
            "success": True,
            "amount_collected": 100.0,
            "tax_type": "income_tax",
            "payer_id": 101,
            "payee_id": 1,
            "error_message": None
        }
        initial_total = government.total_collected_tax
        initial_revenue = government.revenue_this_tick

        # Act
        government.record_revenue(result)

        # Assert
        assert government.total_collected_tax == initial_total + 100.0
        assert government.revenue_this_tick == initial_revenue + 100.0
        assert government.tax_revenue["income_tax"] == 100.0

    def test_record_revenue_failure(self, government):
        # Arrange
        result: TaxCollectionResult = {
            "success": False,
            "amount_collected": 0.0,
            "tax_type": "income_tax",
            "payer_id": 101,
            "payee_id": 1,
            "error_message": "Insufficient funds"
        }
        initial_total = government.total_collected_tax

        # Act
        government.record_revenue(result)

        # Assert
        assert government.total_collected_tax == initial_total
        assert "income_tax" not in government.tax_revenue

    def test_collect_tax_legacy(self, government):
        # Arrange
        payer = MagicMock()
        payer.id = 101
        amount = 50.0
        tax_type = "wealth_tax"
        current_tick = 10

        government.settlement_system.transfer.return_value = True

        # Act
        with pytest.warns(DeprecationWarning, match="Government.collect_tax is deprecated"):
            result = government.collect_tax(amount, tax_type, payer, current_tick)

        # Assert
        government.settlement_system.transfer.assert_called_once_with(
            payer, government, amount, f"{tax_type} collection"
        )

        assert result["success"] is True
        assert result["amount_collected"] == amount
        assert result["tax_type"] == tax_type
        assert government.total_collected_tax == 50.0 # Should have called record_revenue internally

    def test_collect_tax_no_settlement_system(self, government):
        # Arrange
        government.settlement_system = None
        payer = MagicMock()
        payer.id = 101

        # Act
        with pytest.warns(DeprecationWarning):
            result = government.collect_tax(100.0, "tax", payer, 1)

        # Assert
        assert result["success"] is False
        assert result["error_message"] == "No SettlementSystem linked"
