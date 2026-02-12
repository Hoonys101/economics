import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import (
    PortfolioDTO, PortfolioAsset, IFinancialAgent, IPortfolioHandler,
    IHeirProvider
)
from simulation.core_agents import Household
from simulation.agents.government import Government

class MockSettlementAgent(IFinancialAgent, IPortfolioHandler, IHeirProvider):
    pass

# Scenario 1: Standard Inheritance (Cash + Portfolio)
def test_settlement_scenario_1_standard_inheritance(settlement_system, golden_households, government):
    if not golden_households:
        pytest.skip("No golden households found. Please generate fixtures.")

    deceased = MagicMock(spec=MockSettlementAgent)
    heir = MagicMock(spec=MockSettlementAgent)

    # Setup Deceased Agent
    deceased.id = 101
    deceased.assets = 1000

    portfolio_dto = PortfolioDTO(assets=[
        PortfolioAsset(asset_type="stock", asset_id="999", quantity=10.0)
    ])

    # Setup Heir
    heir.id = 102
    heir.get_portfolio = MagicMock()
    heir.clear_portfolio = MagicMock()
    heir.receive_portfolio = MagicMock()
    heir.deposit = MagicMock()
    heir._deposit = MagicMock() # For IFinancialAgent

    # Patch Deceased
    deceased.get_portfolio = MagicMock(return_value=portfolio_dto)
    deceased.clear_portfolio = MagicMock()
    deceased.receive_portfolio = MagicMock()
    deceased.get_heir = MagicMock(return_value=heir.id)
    deceased.withdraw = MagicMock()
    deceased._withdraw = MagicMock() # For IFinancialAgent
    # Mock get_balance for IFinancialAgent compliance
    deceased.get_balance = MagicMock(return_value=1000)

    # Run Create
    account = settlement_system.create_settlement(deceased, tick=100)

    assert account.escrow_cash == 1000
    assert len(account.escrow_portfolio.assets) == 1
    assert account.heir_id == heir.id
    assert not account.is_escheatment

    # Execute
    distribution_plan = [(heir, 1000, "inheritance", "transfer")]
    settlement_system.execute_settlement(deceased.id, distribution_plan, tick=101)

    # Verify
    heir.receive_portfolio.assert_called_once()
    # Verify portfolio passed matches
    received_dto = heir.receive_portfolio.call_args[0][0]
    assert received_dto.assets[0].asset_id == "999"
    assert received_dto.assets[0].quantity == 10.0

    # Check _deposit (IFinancialAgent)
    heir._deposit.assert_called_with(1000)

    # Close
    success = settlement_system.verify_and_close(deceased.id, tick=102)
    assert success
    assert settlement_system.settlement_accounts[deceased.id].status == "CLOSED"

# Scenario 2: Escheatment (No Heir)
def test_settlement_scenario_2_escheatment(settlement_system, golden_households, government):
    if not golden_households:
        pytest.skip("No golden households found")

    deceased = MagicMock(spec=MockSettlementAgent)
    deceased.id = 201
    deceased.assets = 1000

    portfolio_dto = PortfolioDTO(assets=[
        PortfolioAsset(asset_type="stock", asset_id="123", quantity=50.0)
    ])

    deceased.get_portfolio = MagicMock(return_value=portfolio_dto)
    deceased.clear_portfolio = MagicMock()
    deceased.receive_portfolio = MagicMock()
    deceased.get_heir = MagicMock(return_value=None)
    deceased.withdraw = MagicMock()
    deceased._withdraw = MagicMock()
    deceased.get_balance = MagicMock(return_value=1000)

    # Mock Government behavior (spy/mock)
    # Government fixture is a real object with mocked deps.
    # We want to verify it receives portfolio.
    # Government implements receive_portfolio (which adds to self.portfolio).
    # We can check self.portfolio after.
    # But government in fixture has id=1.
    government.id = 1
    # Clear gov portfolio first
    government.portfolio.holdings.clear()

    # Setup Registry for SettlementSystem
    registry = MagicMock()
    registry.get_agent.side_effect = lambda aid: government if aid == government.id else None
    settlement_system.agent_registry = registry

    initial_balance = settlement_system.get_balance(government.id)

    # Run Create
    account = settlement_system.create_settlement(deceased, tick=200)

    assert account.is_escheatment
    assert account.heir_id is None

    # Execute
    # Gov gets everything
    distribution_plan = [(government, 1000, "escheatment", "transfer")]
    settlement_system.execute_settlement(deceased.id, distribution_plan, tick=201)

    # Verify Cash
    # Gov deposit increases assets. But gov fixture assets logic is tricky?
    # Government._add_assets is internal. deposit calls _assets += amount.
    # We can check verify call or just trust it.

    # Verify Portfolio
    # Government should have received the assets
    assert 123 in government.portfolio.holdings
    assert government.portfolio.holdings[123].quantity == 50.0

    # Verify Cash via SettlementSystem (SSoT)
    assert settlement_system.get_balance(government.id) == initial_balance + 1000

    # Close
    success = settlement_system.verify_and_close(deceased.id, tick=202)
    assert success

# Scenario 3: Insolvency (Cash < Claims)
def test_settlement_scenario_3_insolvency(settlement_system, golden_households, government):
    if not golden_households:
        pytest.skip("No golden households found")

    deceased = MagicMock(spec=MockSettlementAgent)
    deceased.id = 301
    deceased.assets = 100

    portfolio_dto = PortfolioDTO(assets=[])

    deceased.get_portfolio = MagicMock(return_value=portfolio_dto)
    deceased.clear_portfolio = MagicMock()
    deceased.receive_portfolio = MagicMock()
    deceased.get_heir = MagicMock(return_value=None)
    deceased.withdraw = MagicMock()
    deceased._withdraw = MagicMock()
    deceased.get_balance = MagicMock(return_value=100)

    account = settlement_system.create_settlement(deceased, tick=300)

    # Plan: Creditor wants 200, but we can only pay 100.
    # The PLAN must reflect reality (LiquidationManager responsibility).
    # But here we simulate that the plan is correctly capped at 100.
    # And verifying SettlementSystem processes it cleanly.

    distribution_plan = [(government, 100, "tax", "transfer")]

    settlement_system.execute_settlement(deceased.id, distribution_plan, tick=301)

    assert account.escrow_cash == 0
    success = settlement_system.verify_and_close(deceased.id, tick=302)
    assert success

    # Test Overdraft Protection
    # If we tried to pay 101...
    deceased.assets = 100
    # Reset mock for new call
    deceased.get_balance = MagicMock(return_value=100)
    deceased._withdraw = MagicMock()

    account_fail = settlement_system.create_settlement(deceased, tick=310)
    plan_fail = [(government, 101, "tax", "transfer")]

    # Capture logs?
    settlement_system.execute_settlement(deceased.id, plan_fail, tick=311)

    # Cash should remain 100 because transfer rejected
    assert account_fail.escrow_cash == 100

    # Close fails because cash remains
    success = settlement_system.verify_and_close(deceased.id, tick=312)
    assert not success
    assert account_fail.status == "CLOSED_WITH_LEAK"
