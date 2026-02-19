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
        # Mocking internals for isolation
        gov.tax_service = MagicMock()
        gov.settlement_system = MagicMock()

        # We need to mock get_total_collected_tax because it's a property that calls tax_service
        gov.tax_service.get_total_collected_tax.return_value = {"USD": 0.0}
        gov.tax_service.get_revenue_this_tick.return_value = {"USD": 0.0}
        gov.tax_service.get_tax_revenue.return_value = {}

        return gov

    def test_record_revenue_delegation(self, government):
        """Test that Government.record_revenue delegates to TaxService."""
        # Arrange
        result: TaxCollectionResult = {
            "success": True,
            "amount_collected": 100.0,
            "tax_type": "income_tax",
            "payer_id": 101,
            "payee_id": 1,
            "error_message": None
        }

        # Act
        government.record_revenue(result)

        # Assert
        government.tax_service.record_revenue.assert_called_once_with(result)

    def test_collect_tax_removed(self, government):
        """Verify that collect_tax is removed."""
        with pytest.raises(AttributeError):
            government.collect_tax(100, "test", MagicMock(), 1)
