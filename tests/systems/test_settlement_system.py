import pytest
from unittest.mock import MagicMock, Mock
from simulation.systems.settlement_system import SettlementSystem
from simulation.dtos.settlement_dtos import EstateSettlementSaga, EstateValuationDTO
from simulation.core_agents import Household
from simulation.agents.government import Government

class TestSettlementSaga:
    @pytest.fixture
    def setup_settlement(self):
        logger = MagicMock()
        bank = MagicMock()
        settlement_system = SettlementSystem(logger=logger, bank=bank)

        state = MagicMock()
        state.agents = {}
        state.time = 10
        state.real_estate_units = []
        state.stock_market = MagicMock()

        return settlement_system, state

    def test_saga_execution_sufficient_cash(self, setup_settlement):
        system, state = setup_settlement

        # Agents
        deceased = MagicMock(spec=Household)
        deceased.id = 101
        deceased._econ_state = MagicMock()
        deceased._econ_state.assets = 50000.0

        # Side effect to track balance
        def withdraw_side_effect(amount):
             deceased._econ_state.assets -= amount
        deceased.withdraw.side_effect = withdraw_side_effect

        heir = MagicMock(spec=Household)
        heir.id = 102
        heir._econ_state = MagicMock()
        heir._econ_state.assets = 0.0

        gov = MagicMock(spec=Government)
        gov.id = 1
        gov.portfolio = MagicMock()

        state.agents = {101: deceased, 102: heir, 1: gov}

        # Saga
        val = EstateValuationDTO(
            cash=50000.0, real_estate_value=0, stock_value=0,
            total_wealth=50000.0, tax_due=10000.0,
            stock_holdings={}, property_holdings=[]
        )
        saga = EstateSettlementSaga(
            deceased_id=101, heir_ids=[102], government_id=1,
            valuation=val, current_tick=10
        )

        # Submit & Execute
        system.submit_saga(saga)
        system.execute(state)

        # Verify
        assert deceased.withdraw.call_count >= 2
        assert gov.deposit.call_count >= 1
        assert heir.deposit.call_count == 1

        # Check system logger for success
        system.logger.info.assert_any_call(
            f"SAGA_COMPLETE | Estate settled for {saga.deceased_id}.",
            extra={"saga_id": saga.id, "deceased_id": saga.deceased_id}
        )

    def test_saga_liquidation_success(self, setup_settlement):
        system, state = setup_settlement

        deceased = MagicMock(spec=Household)
        deceased.id = 101
        deceased._econ_state = MagicMock()
        deceased._econ_state.assets = 1000.0

        def deceased_deposit(amount):
            deceased._econ_state.assets += amount
        def deceased_withdraw(amount):
            deceased._econ_state.assets -= amount

        deceased.deposit.side_effect = deceased_deposit
        deceased.withdraw.side_effect = deceased_withdraw

        deceased._econ_state.portfolio.holdings = {55: MagicMock(quantity=10)}
        deceased._econ_state.portfolio.remove_stock.return_value = MagicMock()

        gov = MagicMock(spec=Government)
        gov.id = 1
        gov.assets = 1000000.0 # Gov rich
        gov.portfolio = MagicMock()

        def gov_withdraw(amount):
            gov.assets -= amount
        gov.withdraw.side_effect = gov_withdraw

        state.agents = {101: deceased, 1: gov}
        state.stock_market.get_daily_avg_price.return_value = 1000.0 # High value

        val = EstateValuationDTO(
            cash=1000.0, real_estate_value=0, stock_value=10000.0,
            total_wealth=11000.0, tax_due=5000.0,
            stock_holdings={55: 10}, property_holdings=[]
        )
        saga = EstateSettlementSaga(
            deceased_id=101, heir_ids=[], government_id=1,
            valuation=val, current_tick=10
        )

        system.submit_saga(saga)
        system.execute(state)

        # Check stock transfer
        deceased._econ_state.portfolio.remove_stock.assert_called_with(55, 10)
        gov.portfolio.add_stock.assert_called()

        system.logger.info.assert_any_call(
            f"SAGA_COMPLETE | Estate settled for {saga.deceased_id}.",
            extra={"saga_id": saga.id, "deceased_id": saga.deceased_id}
        )

    def test_saga_rollback(self, setup_settlement):
        system, state = setup_settlement

        deceased = MagicMock(spec=Household)
        deceased.id = 101
        deceased._econ_state = MagicMock()
        deceased._econ_state.assets = 1000.0

        # Side effects needed for liquidation to succeed initially
        def deceased_deposit(amount):
            deceased._econ_state.assets += amount
        deceased.deposit.side_effect = deceased_deposit

        deceased._econ_state.portfolio.holdings = {55: MagicMock(quantity=10)}
        share_mock = MagicMock()
        deceased._econ_state.portfolio.remove_stock.return_value = share_mock

        gov = MagicMock(spec=Government)
        gov.id = 1
        gov.assets = 1000000.0 # Gov rich
        gov.portfolio = MagicMock()

        state.agents = {101: deceased, 1: gov}
        state.stock_market.get_daily_avg_price.return_value = 200.0 # 10 * 200 = 2000

        # Configure Bank to fail for the TAX payment (5000)
        # Deceased will have 1000 (init) + 2000 (liquidation) = 3000.
        # Tax = 5000.
        # Deceased needs 2000 from Bank.
        # Bank fails.
        system.bank.get_balance.return_value = 0.0
        system.bank.withdraw_for_customer.return_value = False

        val = EstateValuationDTO(
            cash=1000.0, real_estate_value=0, stock_value=2000.0,
            total_wealth=3000.0, tax_due=5000.0,
            stock_holdings={55: 10}, property_holdings=[]
        )
        saga = EstateSettlementSaga(
            deceased_id=101, heir_ids=[], government_id=1,
            valuation=val, current_tick=10
        )

        system.submit_saga(saga)
        system.execute(state)

        # Verify Rollback
        system.logger.warning.assert_any_call(f"SAGA_ROLLBACK | Rolling back liquidation for {deceased.id}.")

        # Check Stock Return
        gov.portfolio.remove_stock.assert_called_with(55, 10)
        deceased._econ_state.portfolio.add_stock.assert_called()
