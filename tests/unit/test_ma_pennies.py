import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.systems.ma_manager import MAManager
from simulation.firms import Firm
from simulation.finance.api import ISettlementSystem, IMonetaryAuthority
from modules.system.api import DEFAULT_CURRENCY

class TestMAManagerPennies:

    @pytest.fixture
    def mock_simulation(self):
        sim = MagicMock()
        sim.firms = []
        sim.agents = {}
        # WO-178: Escheatment Logic
        # Direct government singleton for testing purposes
        sim.government = MagicMock()
        # Make sure simulation has settlement_system attribute if checked
        sim.settlement_system = MagicMock(spec=IMonetaryAuthority)
        return sim

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.MA_ENABLED = True
        config.BANKRUPTCY_CONSECUTIVE_LOSS_TICKS = 20
        config.HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7
        config.HOSTILE_TAKEOVER_PREMIUM = 1.2
        config.FRIENDLY_MERGER_PREMIUM = 1.1
        config.MIN_ACQUISITION_CASH_RATIO = 1.5
        config.HOSTILE_TAKEOVER_SUCCESS_PROB = 1.0 # Force success for testing
        config.MERGER_EMPLOYEE_RETENTION_RATES = [0.5, 0.5]
        return config

    @pytest.fixture
    def mock_settlement(self):
        # We use strict spec to ensure we are mocking the real interface
        return MagicMock(spec=IMonetaryAuthority)

    def test_friendly_merger_price_is_int(self, mock_simulation, mock_config, mock_settlement):
        """
        Verify that Friendly Merger calls settlement_system.transfer with an integer amount (pennies).
        """
        manager = MAManager(mock_simulation, mock_config, settlement_system=mock_settlement)

        # Setup Predator
        predator = MagicMock(spec=Firm)
        predator.id = 101
        predator.is_active = True
        predator.wallet.get_balance.return_value = 10_000_000 # Wealthy ($100k)
        predator.finance_state = MagicMock()
        predator.finance_state.current_profit = {DEFAULT_CURRENCY: 1000}
        predator.finance_state.consecutive_loss_turns = 0
        predator.finance_state.valuation_pennies = 10_000_000
        predator.valuation = 10_000_000
        predator.get_market_cap.return_value = 100_000.0
        predator.system2_planner = None
        predator.hr_engine = MagicMock()
        predator.hr_state = MagicMock()
        predator.automation_level = 1.0

        # Setup Prey (Friendly Merger Target, NOT Hostile)
        # To avoid hostile: Market Cap > Valuation * Threshold
        # Valuation = 500,000 ($5k). Threshold 0.7. Limit = 350,000.
        # Set Market Cap = 400,000 ($4k).
        prey = MagicMock(spec=Firm)
        prey.id = 202
        prey.is_active = True
        prey.wallet.get_balance.return_value = 100 # Poor
        prey.finance_state = MagicMock()
        prey.finance_state.consecutive_loss_turns = 25 # Trigger distress
        prey.finance_state.valuation_pennies = 500_000
        prey.valuation = 500_000
        prey.get_market_cap.return_value = 400_000.0
        prey.founder_id = 999
        prey.get_all_items.return_value = {}
        prey.hr_state = MagicMock()
        prey.hr_state.employees = []
        prey.hr_engine = MagicMock()
        prey.automation_level = 0.5

        mock_simulation.agents[999] = MagicMock()
        mock_simulation.firms = [predator, prey]

        # Execute
        manager.process_market_exits_and_entries(current_tick=100)

        # Assertions
        transfer_calls = mock_settlement.transfer.call_args_list

        found_friendly = False
        for args, kwargs in transfer_calls:
            memo = args[3] if len(args) > 3 else kwargs.get('memo', '')
            if "M&A Acquisition" in memo:
                found_friendly = True
                amount = args[2] if len(args) > 2 else kwargs.get('amount')
                print(f"Transfer amount type: {type(amount)}, value: {amount}")
                assert isinstance(amount, int), f"Merger price must be int, got {type(amount)}"
                # Friendly Price: Valuation * Premium = 500,000 * 1.1 = 550,000
                assert amount == 550_000

        assert found_friendly, "Friendly Merger transfer not found"

    def test_hostile_takeover_price_is_int(self, mock_simulation, mock_config, mock_settlement):
        """
        Verify that Hostile Takeover calls settlement_system.transfer with an integer amount (pennies).
        """
        manager = MAManager(mock_simulation, mock_config, settlement_system=mock_settlement)

        # Ensure config values are not Mocks if something went wrong with fixture
        mock_config.HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7
        mock_config.HOSTILE_TAKEOVER_PREMIUM = 1.2
        mock_config.HOSTILE_TAKEOVER_SUCCESS_PROB = 1.0

        # Setup Predator
        predator = MagicMock(spec=Firm)
        predator.id = 101
        predator.is_active = True
        predator.wallet.get_balance.return_value = 10_000_000 # Wealthy ($100k)
        predator.finance_state = MagicMock()
        predator.finance_state.consecutive_loss_turns = 0
        predator.finance_state.current_profit = {DEFAULT_CURRENCY: 1000}
        predator.finance_state.valuation_pennies = 10_000_000
        predator.valuation = 10_000_000
        predator.get_market_cap.return_value = 100_000.0
        predator.system2_planner = None
        predator.hr_engine = MagicMock()
        predator.hr_state = MagicMock()
        predator.automation_level = 1.0

        # Setup Hostile Target
        # Market Cap < Intrinsic Value * Threshold
        target = MagicMock(spec=Firm)
        target.id = 303
        target.is_active = True
        target.wallet.get_balance.return_value = 0 # Poor target, lowers avg_assets
        target.finance_state = MagicMock()
        target.finance_state.consecutive_loss_turns = 0
        target.finance_state.current_profit = {DEFAULT_CURRENCY: 0}

        # Intrinsic Value: 1,000,000 pennies ($10,000)
        target.finance_state.valuation_pennies = 1_000_000
        target.valuation = 1_000_000

        # Market Cap: $5,000 (Undervalued, 0.5 ratio < 0.7 threshold)
        target.get_market_cap.return_value = 500_000.0

        target.founder_id = 888
        target.get_all_items.return_value = {}
        target.hr_state = MagicMock()
        target.hr_state.employees = []
        target.hr_engine = MagicMock()
        target.automation_level = 0.5

        mock_simulation.agents[888] = MagicMock()
        mock_simulation.firms = [predator, target]

        # Execute
        manager.process_market_exits_and_entries(current_tick=100)

        # Assertions
        transfer_calls = mock_settlement.transfer.call_args_list
        found_hostile = False
        for args, kwargs in transfer_calls:
            memo = args[3] if len(args) > 3 else kwargs.get('memo', '')
            if "M&A Acquisition" in memo:
                found_hostile = True
                amount = args[2] if len(args) > 2 else kwargs.get('amount')
                print(f"Hostile Transfer amount type: {type(amount)}, value: {amount}")
                assert isinstance(amount, int), f"Merger price must be int, got {type(amount)}"

                # Logic: market_cap (dollars) * premium (1.2) * 100 (pennies)
                # 5,000.0 * 1.2 * 100 = 6,000.0 * 100 = 600,000 pennies
                assert amount == 600_000

        assert found_hostile, "Hostile Takeover transfer not found"

    def test_bankruptcy_liquidation_values_are_int(self, mock_simulation, mock_config, mock_settlement):
        """
        Verify that MAManager calls settlement_system.record_liquidation with integer values.
        """
        manager = MAManager(mock_simulation, mock_config, settlement_system=mock_settlement)

        # Setup Bankrupt Firm
        bankrupt = MagicMock(spec=Firm)
        bankrupt.id = 303
        bankrupt.is_active = True
        bankrupt.wallet.get_balance.return_value = -100 # Bankrupt condition
        bankrupt.calculate_valuation.return_value = 0
        bankrupt.hr_state = MagicMock()
        bankrupt.hr_state.employees = []

        # Setup Assets
        bankrupt.capital_stock = 5000.50 # Float capital (dollars)
        bankrupt.get_all_items.return_value = {'apple': 10.5} # Float quantity

        # Mock Market for price
        market_mock = MagicMock()
        market_mock.avg_price = 20.5 # Float price (dollars)
        mock_simulation.markets = {'apple': market_mock}

        # Mock liquidate_assets return
        # Returns Dict[CurrencyCode, int]
        bankrupt.liquidate_assets.return_value = {DEFAULT_CURRENCY: 12345} # 12345 pennies recovered

        # Update firms list
        mock_simulation.firms = [bankrupt]

        # Execute
        manager.process_market_exits_and_entries(current_tick=100)

        # Assertions
        # verify record_liquidation call
        calls = mock_settlement.record_liquidation.call_args_list
        assert len(calls) > 0, "record_liquidation not called"

        args, kwargs = calls[0]

        inv_val = kwargs.get('inventory_value')
        cap_val = kwargs.get('capital_value')
        rec_cash = kwargs.get('recovered_cash')

        print(f"Inventory Value: {type(inv_val)} {inv_val}")
        print(f"Capital Value: {type(cap_val)} {cap_val}")
        print(f"Recovered Cash: {type(rec_cash)} {rec_cash}")

        assert isinstance(inv_val, int), f"Inventory value must be int, got {type(inv_val)}"
        assert isinstance(cap_val, int), f"Capital value must be int, got {type(cap_val)}"

        # Expected calculation:
        # Inv: 10.5 * 20.5 * 100 = 215.25 * 100 = 21525 pennies
        assert inv_val == 21525

        # Cap: 5000.50 * 100 = 500050 pennies
        assert cap_val == 500050

        assert isinstance(rec_cash, int), f"Recovered cash MUST be int, got {type(rec_cash)}"
        assert rec_cash == 0 # Logic passes 0 to record_liquidation
