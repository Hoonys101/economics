import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from modules.government.dtos import FiscalPolicyDTO
from simulation.dtos.api import MarketSnapshotDTO

class TestGovernmentFiscalIntegration:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        config.TAX_BRACKETS = [(1.0, 0.10)] # Simple flat 10% for easy test
        config.TICKS_PER_YEAR = 100
        config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        config.INCOME_TAX_RATE = 0.1
        config.CORPORATE_TAX_RATE = 0.2
        config.CB_INFLATION_TARGET = 0.02
        config.AUTO_COUNTER_CYCLICAL_ENABLED = True
        config.FISCAL_SENSITIVITY_ALPHA = 0.5
        return config

    def test_calculate_income_tax_uses_fiscal_policy_manager(self, mock_config):
        # Setup
        gov = Government(id=1, config_module=mock_config)

        # Override manager with a mock to verify delegation
        gov.tax_service.fiscal_policy_manager = MagicMock()
        gov.tax_service.fiscal_policy_manager.calculate_tax_liability.return_value = 123

        # Ensure a policy is set
        gov.fiscal_policy = MagicMock(spec=FiscalPolicyDTO)

        # Execute
        tax = gov.calculate_income_tax(1000, 10)

        # Verify
        assert tax == 123
        gov.tax_service.fiscal_policy_manager.calculate_tax_liability.assert_called_once_with(gov.fiscal_policy, 1000)

    def test_make_policy_decision_updates_fiscal_policy(self, mock_config):
        # Setup
        gov = Government(id=1, config_module=mock_config)

        # Mock the tax service's fiscal policy manager
        # Government.make_policy_decision orchestrates fiscal_engine and tax_service

        gov.tax_service.fiscal_policy_manager = MagicMock()
        expected_policy = FiscalPolicyDTO(tax_brackets=[], income_tax_rate=0.1, corporate_tax_rate=0.2)
        gov.tax_service.fiscal_policy_manager.determine_fiscal_stance.return_value = expected_policy

        # Setup market data
        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 20.0
            }
        }

        # Execute
        # We need a dummy CentralBank
        cb = MagicMock()
        gov.sensory_data = MagicMock() # Need sensory data for policy engine
        gov.sensory_data.current_gdp = 1000.0
        gov.sensory_data.inflation_sma = 0.02
        gov.sensory_data.gdp_growth_sma = 0.05
        gov.make_policy_decision(market_data, 1, cb)

        # Verify
        assert gov.fiscal_policy == expected_policy

        # Check if determine_fiscal_stance was called with correct snapshot
        args, _ = gov.tax_service.fiscal_policy_manager.determine_fiscal_stance.call_args
        snapshot = args[0]
        assert isinstance(snapshot, MarketSnapshotDTO)
        # Check market_data field (legacy support) since MarketSnapshotDTO doesn't have prices attribute
        assert snapshot.market_data["goods_market"]["basic_food_current_sell_price"] == 20.0
