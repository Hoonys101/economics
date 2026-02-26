import pytest
from unittest.mock import MagicMock, Mock
from simulation.systems.ma_manager import MAManager
from modules.finance.utils.currency_math import round_to_pennies
from modules.finance.api import IFinancialAgent, IMonetaryAuthority
from modules.system.api import DEFAULT_CURRENCY

class TestMAManagerPennies:
    @pytest.fixture
    def mock_simulation(self):
        sim = MagicMock()
        # Mock Settlement System satisfying IMonetaryAuthority check
        sim.settlement_system = MagicMock(spec=IMonetaryAuthority)
        sim.agents = {}
        sim.firms = []
        return sim

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.MA_ENABLED = True
        config.HOSTILE_TAKEOVER_PREMIUM = 1.2
        config.FRIENDLY_MERGER_PREMIUM = 1.1
        config.MIN_ACQUISITION_CASH_RATIO = 1.5
        config.BANKRUPTCY_CONSECUTIVE_LOSS_TICKS = 20
        # Add HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD default
        config.HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7
        return config

    def test_valuation_rounding(self, mock_simulation, mock_config):
        """
        Verify that M&A valuations are rounded to pennies strictly.
        """
        manager = MAManager(mock_simulation, mock_config)

        # Mock Firms
        predator = MagicMock()
        predator.id = 1
        predator.wallet.get_balance.return_value = 1000000 # 10k pennies ($100)
        predator.finance_state.consecutive_loss_turns = 0 # Healthy
        predator.finance_state.valuation_pennies = 1000000
        predator.get_market_cap.return_value = 1000000
        predator.finance_state.current_profit = {DEFAULT_CURRENCY: 100}
        predator.is_active = True
        predator.automation_level = 1.0

        prey = MagicMock()
        prey.id = 2
        prey.wallet.get_balance.return_value = 50000 # 500 pennies
        prey.valuation = 50055 # 500.55 pennies (Wait, valuation should be int pennies)
        prey.get_market_cap.return_value = 50055
        prey.finance_state.valuation_pennies = 50055
        prey.finance_state.consecutive_loss_turns = 25 # Trigger distress
        prey.is_active = True
        prey.automation_level = 1.0

        # Setup Logic
        mock_simulation.firms = [predator, prey]

        # Trigger M&A Logic (Force Friendly)

        # Mock Settlement System Transfer
        # Access via manager.settlement_system which is set in __init__
        manager.settlement_system.transfer = MagicMock()

        # Run
        manager.process_market_exits_and_entries(current_tick=100)

        # Verify Transfer Amount is int
        # Offer = Valuation * Premium (1.1)
        # 50055 * 1.1 = 55060.5 -> Should round to 55060 (Half to Even) or 55061?
        # round_to_pennies(55060.5) -> 55060 (if nearest even) or 55061?
        # Python 3 round(x.5) rounds to nearest even.
        # 55060 is even. So 55060.

        # Check if transfer was called
        # Note: Depending on logic flow, it might pick predator or not.
        # Check logic:
        # Predator Criteria: balance > avg_assets * 1.5 and profit > 0
        # avg_assets = (1000000 + 50000) / 2 = 525000
        # Predator 1000000 > 525000 * 1.5 (787500). YES.

        assert manager.settlement_system.transfer.called
        args, kwargs = manager.settlement_system.transfer.call_args
        amount = args[2] # transfer(predator, prey, amount, ...)

        assert isinstance(amount, int)
        # 50055 * 1.1 = 55060.5... (Float drift) -> Rounds to 55061
        # Expected: 55061
        assert amount == 55061

    def test_hostile_takeover_rounding(self, mock_simulation, mock_config):
        """
        Verify hostile takeover valuation rounding.
        """
        manager = MAManager(mock_simulation, mock_config)
        mock_config.HOSTILE_TAKEOVER_PREMIUM = 1.2
        mock_config.HOSTILE_TAKEOVER_SUCCESS_PROB = 1.0 # Force success

        predator = MagicMock()
        predator.id = 1
        predator.wallet.get_balance.return_value = 1000000
        predator.finance_state.current_profit = {DEFAULT_CURRENCY: 100} # Profitable
        predator.finance_state.consecutive_loss_turns = 0
        predator.finance_state.valuation_pennies = 1000000
        predator.get_market_cap.return_value = 1000000
        predator.is_active = True
        predator.automation_level = 1.0

        target = MagicMock()
        target.id = 2
        target.wallet.get_balance.return_value = 50000
        target.get_market_cap.return_value = 10000 # 100.00 pennies
        target.finance_state.valuation_pennies = 20000 # Intrinsic > Market Cap (Undervalued)
        target.finance_state.current_profit = {DEFAULT_CURRENCY: -10}
        target.finance_state.consecutive_loss_turns = 0
        target.is_active = True
        target.automation_level = 1.0

        mock_simulation.firms = [predator, target]

        manager.settlement_system.transfer = MagicMock()

        manager.process_market_exits_and_entries(current_tick=100)

        assert manager.settlement_system.transfer.called
        args, kwargs = manager.settlement_system.transfer.call_args
        amount = args[2]

        assert isinstance(amount, int)
        # 10000 * 1.2 = 12000.0 -> 12000
        assert amount == 12000
