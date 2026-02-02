import pytest
from unittest.mock import MagicMock
from simulation.world_state import WorldState
from simulation.bank import Bank, Deposit, Loan
from simulation.agents.government import Government
from simulation.agents.central_bank import CentralBank
from simulation.core_agents import Household
from simulation.systems.settlement_system import SettlementSystem
from modules.common.config_manager.api import ConfigManager

class TestM2Integrity:
    @pytest.fixture
    def setup_world(self):
        # Config Mock
        config_manager = MagicMock(spec=ConfigManager)
        config_module = MagicMock()
        config_module.INITIAL_BASE_ANNUAL_RATE = 0.05
        config_module.CB_UPDATE_INTERVAL = 10
        config_module.CB_INFLATION_TARGET = 0.02
        config_module.CB_TAYLOR_ALPHA = 1.5
        config_module.CB_TAYLOR_BETA = 0.5
        config_module.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0

        # Set default config values to avoid validation errors
        config_manager.get.side_effect = lambda k, d=None: d
        logger = MagicMock()
        repo = MagicMock()

        # WorldState
        state = WorldState(config_manager, config_module, logger, repo)

        # Settlement System
        settlement_system = SettlementSystem(logger)
        state.settlement_system = settlement_system

        # Agents Setup
        # 1. Central Bank
        cb = CentralBank(tracker=MagicMock(), config_module=config_module)
        cb.id = "CENTRAL_BANK"
        state.central_bank = cb
        # Initialize CB Cash (M0 issuer starts with 0 or negative, but let's say it issued initial money)
        # Actually in this sim, CB mints by 'deposit' or 'withdraw' (negative).
        # Let's assume genesis happened and CB has some state if needed.
        # For now, let's keep it clean.

        # 2. Government
        gov = Government(id=0, initial_assets=1000.0, config_module=config_module)
        gov.settlement_system = settlement_system
        state.government = gov

        # 3. Bank
        bank = Bank(id=1, initial_assets=5000.0, config_manager=config_manager, settlement_system=settlement_system)
        bank.set_government(gov)
        state.bank = bank

        # 4. Household
        hh = MagicMock(spec=Household)
        hh.id = 2

        # Explicitly Mock Sub-States (TD-Mock-Household)
        hh._bio_state = MagicMock()
        hh._bio_state.is_active = True
        hh._econ_state = MagicMock()
        hh._econ_state.assets = 1000.0  # Initialize as float for calculation
        hh._social_state = MagicMock()

        hh.assets = 1000.0
        hh.is_active = True
        hh.settlement_system = settlement_system

        # Household must support withdraw/deposit for SettlementSystem
        # And keep _econ_state.assets in sync for WorldState calculations
        def withdraw(amount):
            hh.assets -= amount
            hh._econ_state.assets -= amount

        def deposit(amount):
            hh.assets += amount
            hh._econ_state.assets += amount

        hh.withdraw = withdraw
        hh.deposit = deposit

        state.households.append(hh)
        state.agents[hh.id] = hh
        state.agents[gov.id] = gov
        state.agents[bank.id] = bank
        state.agents[cb.id] = cb # CB ID is string usually

        return state, cb, gov, bank, hh

    def test_credit_expansion(self, setup_world):
        state, cb, gov, bank, hh = setup_world

        initial_m2 = state.calculate_total_money()

        # Grant Loan
        loan_amount = 500.0
        loan_info, tx = bank.grant_loan(str(hh.id), loan_amount, 0.05)

        assert loan_info is not None
        assert tx.transaction_type == "credit_creation"

        # Verify M2 Increase
        final_m2 = state.calculate_total_money()
        assert final_m2 == initial_m2 + loan_amount

        # Verify M0 Integrity (if implemented)
        if hasattr(state, "calculate_base_money"):
            m0 = state.calculate_base_money()
            # M0 = Currency (Gov 1000 + HH 1000) + Reserves (Bank 5000) = 7000
            assert m0 == 7000.0

            # Formula Check: M2 = M0 + Credit - BankEquity
            # Credit = 500. BankEquity = 5000.
            # M2 = 2500.
            # 7000 + 500 - 5000 = 2500. Correct.
            pass

    def test_credit_destruction(self, setup_world):
        state, cb, gov, bank, hh = setup_world

        # Setup: Grant Loan
        loan_amount = 500.0
        bank.grant_loan(str(hh.id), loan_amount, 0.05)
        m2_after_loan = state.calculate_total_money()

        # Repay/Void Loan
        loan_id = list(bank.loans.keys())[0]
        bank.void_loan(loan_id)

        m2_after_void = state.calculate_total_money()
        assert m2_after_void == m2_after_loan - loan_amount

    def test_settlement_purity(self, setup_world):
        state, cb, gov, bank, hh = setup_world

        initial_m2 = state.calculate_total_money()
        amount = 100.0

        # Use SettlementSystem
        # We need to make sure SettlementSystem can handle the mock objects
        # gov and bank are real objects (or close), hh is MagicMock but patched with withdraw/deposit.

        res = state.settlement_system.transfer(gov, hh, amount, "Test Transfer")
        assert res is not None

        # Check balances
        assert gov.assets == 900.0
        assert hh.assets == 1100.0

        final_m2 = state.calculate_total_money()
        assert final_m2 == initial_m2

    def test_m0_integrity(self, setup_world):
        state, cb, gov, bank, hh = setup_world

        if not hasattr(state, "calculate_base_money"):
            pytest.skip("calculate_base_money not implemented yet")

        initial_m0 = state.calculate_base_money()
        # Expect M0 = 1000(Gov) + 1000(HH) + 5000(Bank) = 7000
        assert initial_m0 == 7000.0

        # 1. Credit Expansion should NOT change M0
        bank.grant_loan(str(hh.id), 500.0, 0.05)
        m0_after_loan = state.calculate_base_money()
        assert m0_after_loan == initial_m0

        # 2. Settlement Transfer should NOT change M0
        state.settlement_system.transfer(gov, hh, 100.0, "Tx")
        m0_after_tx = state.calculate_base_money()
        assert m0_after_tx == initial_m0

        # 3. Central Bank OMO (Purchase Bond) -> Increases M0
        # CB buys something from Govt for 100.
        # Use settlement system mint_and_transfer or similar logic if CB has it.
        # CB.purchase_bonds just adds bond to list.
        # We need the cash flow.
        # Manually simulate OMO cash flow:
        # CB creates money (withdraws into negative or uses 'mint')
        # Here we use SettlementSystem.create_and_transfer (Minting)

        state.settlement_system.create_and_transfer(cb, gov, 200.0, "OMO Purchase", 0)

        m0_after_omo = state.calculate_base_money()
        # Gov assets increased by 200.
        # M0 should increase by 200.
        assert m0_after_omo == initial_m0 + 200.0
