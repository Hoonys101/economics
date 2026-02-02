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
        market_data = {'goods_market': {'basic_food_current_sell_price': 10.0}}
        snapshot = MarketSnapshotDTO(tick=1, market_signals={}, market_data=market_data)

        # Execute
        policy = manager.determine_fiscal_stance(snapshot)

        # Verify
        # Survival cost = 10.0 * 1.0 = 10.0
        # Bracket 1: Ceiling = 1.0 * 10.0 = 10.0
        # Bracket 2: Ceiling = 3.0 * 10.0 = 30.0

        assert len(policy.progressive_tax_brackets) == 3

        b1 = policy.progressive_tax_brackets[0]
        assert b1.floor == 0.0
        assert b1.ceiling == 10.0
        assert b1.rate == 0.0

        b2 = policy.progressive_tax_brackets[1]
        assert b2.floor == 10.0
        assert b2.ceiling == 30.0
        assert b2.rate == 0.10

        b3 = policy.progressive_tax_brackets[2]
        assert b3.floor == 30.0
        assert b3.ceiling is None
        assert b3.rate == 0.20

    def test_determine_fiscal_stance_defaults_if_no_config(self):
        # Setup config with no TAX_BRACKETS
        config = MagicMock()
        config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
        config.TAX_BRACKETS = []
        manager = FiscalPolicyManager(config)

        market_data = {'goods_market': {'basic_food_current_sell_price': 10.0}}
        snapshot = MarketSnapshotDTO(tick=1, market_signals={}, market_data=market_data)

        policy = manager.determine_fiscal_stance(snapshot)

        # Should use defaults (1.0/0.0, 3.0/0.10, inf/0.20)
        assert len(policy.progressive_tax_brackets) == 3
        assert policy.progressive_tax_brackets[1].rate == 0.10

    def test_calculate_tax_liability_progressive(self, manager):
        # Setup
        brackets = [
            TaxBracketDTO(floor=0.0, rate=0.0, ceiling=10.0),
            TaxBracketDTO(floor=10.0, rate=0.10, ceiling=30.0),
            TaxBracketDTO(floor=30.0, rate=0.20, ceiling=None)
        ]
        policy = FiscalPolicyDTO(progressive_tax_brackets=brackets)

        # Test Case 1: Income below first ceiling (Tax Free)
        assert manager.calculate_tax_liability(policy, 5.0) == 0.0

        # Test Case 2: Income exactly at first ceiling
        assert manager.calculate_tax_liability(policy, 10.0) == 0.0

        # Test Case 3: Income in second bracket (10%)
        # Income 20. Taxable: 20 - 10 = 10. Tax: 10 * 0.10 = 1.0
        assert manager.calculate_tax_liability(policy, 20.0) == 1.0

        # Test Case 4: Income exactly at second ceiling
        # Income 30. Bracket 1: 0. Bracket 2: (30-10)*0.1 = 2.0.
        assert manager.calculate_tax_liability(policy, 30.0) == 2.0

        # Test Case 5: Income in third bracket (20%)
        # Income 40. Bracket 1: 0. Bracket 2: 2.0. Bracket 3: (40-30)*0.2 = 2.0. Total = 4.0
        assert manager.calculate_tax_liability(policy, 40.0) == 4.0

    def test_calculate_tax_liability_zero_or_negative(self, manager):
        policy = FiscalPolicyDTO(progressive_tax_brackets=[])
        assert manager.calculate_tax_liability(policy, 0.0) == 0.0
        assert manager.calculate_tax_liability(policy, -100.0) == 0.0
