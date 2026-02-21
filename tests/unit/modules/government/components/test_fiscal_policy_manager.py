import pytest
from unittest.mock import Mock, MagicMock
from modules.government.components.fiscal_policy_manager import FiscalPolicyManager
from modules.government.dtos import FiscalPolicyDTO, TaxBracketDTO
from simulation.dtos.api import MarketSnapshotDTO

class TestFiscalPolicyManager:
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        config.TAX_BRACKETS = [
            (1.0, 0.0),    # 0% up to 1x survival
            (3.0, 0.10),   # 10% from 1x to 3x survival
            (float('inf'), 0.20) # 20% above 3x survival
        ]
        return config

    @pytest.fixture
    def manager(self, mock_config):
        return FiscalPolicyManager(mock_config)

    def test_determine_fiscal_stance_calculates_survival_cost_correctly(self, manager, mock_config):
        # Setup
        # Input 10.0 (Dollars) is converted to 1000 pennies inside manager (10.0 * 100)
        market_data = {'goods_market': {'basic_food_current_sell_price': 10.0}} # $10
        snapshot = MarketSnapshotDTO(tick=1, market_signals={}, market_data=market_data)

        # Execute
        policy = manager.determine_fiscal_stance(snapshot)

        # Verify
        # Survival cost = 1000.0 * 1.0 = 1000
        # Bracket 1: Threshold = 0 (Start)
        # Bracket 2: Threshold = 1.0 * 1000 = 1000
        # Bracket 3: Threshold = 3.0 * 1000 = 3000

        assert len(policy.tax_brackets) == 3

        b1 = policy.tax_brackets[0]
        assert b1.threshold == 0
        assert b1.rate == 0.0

        b2 = policy.tax_brackets[1]
        assert b2.threshold == 1000
        assert b2.rate == 0.10

        b3 = policy.tax_brackets[2]
        assert b3.threshold == 3000
        assert b3.rate == 0.20

    def test_determine_fiscal_stance_defaults_if_no_config(self):
        # Setup config with no TAX_BRACKETS
        config = MagicMock()
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        config.TAX_BRACKETS = []
        manager = FiscalPolicyManager(config)

        market_data = {'goods_market': {'basic_food_current_sell_price': 1000.0}}
        snapshot = MarketSnapshotDTO(tick=1, market_signals={}, market_data=market_data)

        policy = manager.determine_fiscal_stance(snapshot)

        # Should use defaults (1.0/0.0, 3.0/0.10, inf/0.20)
        assert len(policy.tax_brackets) == 3
        assert policy.tax_brackets[1].rate == 0.10

    def test_calculate_tax_liability_progressive(self, manager):
        # Setup
        # Brackets: 0-10 free, 10-30 @ 10%, 30+ @ 20%
        brackets = [
            TaxBracketDTO(threshold=0, rate=0.0),
            TaxBracketDTO(threshold=10, rate=0.10),
            TaxBracketDTO(threshold=30, rate=0.20)
        ]
        policy = FiscalPolicyDTO(tax_brackets=brackets)

        # Test Case 1: Income below first threshold (5) -> Wait, threshold 0.
        # 5 > 0. Taxable 5. Rate 0. Tax 0.
        assert manager.calculate_tax_liability(policy, 5) == 0

        # Test Case 2: Income exactly at second threshold (10)
        # 10 > 0. Taxable 10. Rate 0. Tax 0.
        assert manager.calculate_tax_liability(policy, 10) == 0

        # Test Case 3: Income in second bracket (20)
        # 20. Sort DESC: 30, 10, 0.
        # Bracket 30: 20 < 30. Skip.
        # Bracket 10: 20 > 10. Taxable 10. Tax 10*0.1=1. Remainder 10.
        # Bracket 0: 10 > 0. Taxable 10. Tax 10*0.0=0. Remainder 0.
        # Total 1.
        assert manager.calculate_tax_liability(policy, 20) == 1

        # Test Case 4: Income exactly at third threshold (30)
        # Bracket 30: 30 <= 30. Skip.
        # Bracket 10: 30 > 10. Taxable 20. Tax 2. Remainder 10.
        # Bracket 0: 10 > 0. Taxable 10. Tax 0.
        # Total 2.
        assert manager.calculate_tax_liability(policy, 30) == 2

        # Test Case 5: Income in third bracket (40)
        # Bracket 30: 40 > 30. Taxable 10. Tax 2. Remainder 30.
        # Bracket 10: 30 > 10. Taxable 20. Tax 2. Remainder 10.
        # Bracket 0: 10 > 0. Taxable 10. Tax 0.
        # Total 4.
        assert manager.calculate_tax_liability(policy, 40) == 4

    def test_calculate_tax_liability_zero_or_negative(self, manager):
        policy = FiscalPolicyDTO(tax_brackets=[])
        assert manager.calculate_tax_liability(policy, 0) == 0
        assert manager.calculate_tax_liability(policy, -100) == 0
