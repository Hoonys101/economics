import pytest
from unittest.mock import MagicMock, ANY
from modules.governance.judicial.system import JudicialSystem
from modules.system.event_bus.event_bus import EventBus
from modules.events.dtos import LoanDefaultedEvent
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry
from modules.finance.api import IShareholderRegistry, IPortfolioHandler, ICreditFrozen, IFinancialEntity
from modules.simulation.api import IEducated

class MockAgent:
    def __init__(self, id):
        self.id = id
        self.education_xp = 100.0
        self._credit_frozen_until_tick = 0
        self._assets = 500.0 # Liquid assets

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int):
        self._credit_frozen_until_tick = value

    def get_portfolio(self):
        # Mock portfolio
        mock_portfolio = MagicMock()
        mock_asset = MagicMock()
        mock_asset.asset_type = 'stock'
        mock_asset.asset_id = '99' # Firm ID
        mock_portfolio.assets = [mock_asset]
        return mock_portfolio

    def clear_portfolio(self):
        pass

    def receive_portfolio(self, portfolio):
        pass

    @property
    def assets(self) -> float:
        return self._assets

    def deposit(self, amount, currency="USD"): pass
    def withdraw(self, amount, currency="USD"): pass
    def get_balance(self, currency="USD"): return self._assets

# Make MockAgent satisfy protocols virtually for isinstance checks if needed
# But since Python uses duck typing or explicit registration, we might need to register.
# However, JudicialSystem uses isinstance(agent, Protocol).
# This requires @runtime_checkable and the class to implement methods.
# My MockAgent implements them.

@pytest.fixture
def mock_dependencies():
    event_bus = EventBus()
    settlement_system = MagicMock(spec=ISettlementSystem)
    agent_registry = MagicMock(spec=IAgentRegistry)
    shareholder_registry = MagicMock(spec=IShareholderRegistry)
    config_manager = MagicMock()

    # Setup Config defaults
    def get_config(key, default=None):
        return default
    config_manager.get.side_effect = get_config

    return {
        "event_bus": event_bus,
        "settlement_system": settlement_system,
        "agent_registry": agent_registry,
        "shareholder_registry": shareholder_registry,
        "config_manager": config_manager
    }

def test_judicial_system_handles_loan_default(mock_dependencies):
    deps = mock_dependencies
    system = JudicialSystem(
        event_bus=deps["event_bus"],
        settlement_system=deps["settlement_system"],
        agent_registry=deps["agent_registry"],
        shareholder_registry=deps["shareholder_registry"],
        config_manager=deps["config_manager"]
    )

    # Setup Agent
    agent_id = 1
    creditor_id = 2
    agent = MockAgent(agent_id)
    creditor = MockAgent(creditor_id)

    deps["agent_registry"].get_agent.side_effect = lambda aid: agent if aid == agent_id else (creditor if aid == creditor_id else None)

    # Event
    event: LoanDefaultedEvent = {
        "event_type": "LOAN_DEFAULTED",
        "tick": 10,
        "agent_id": agent_id,
        "loan_id": "loan_1",
        "defaulted_amount": 1000.0,
        "creditor_id": creditor_id
    }

    # Publish Event
    deps["event_bus"].publish(event)

    # Assertions

    # 1. XP Penalty (Default 0.2)
    # 100 * (1 - 0.2) = 80
    assert agent.education_xp == 80.0

    # 2. Credit Freeze (Default 100 ticks)
    # 10 + 100 = 110
    assert agent.credit_frozen_until_tick == 110

    # 3. Share Seizure
    # Should call shareholder_registry.register_shares(99, agent_id, 0)
    deps["shareholder_registry"].register_shares.assert_called_with(99, agent_id, 0)

    # 4. Asset Seizure (Transfer)
    # Agent has 500. Seize all.
    deps["settlement_system"].transfer.assert_called_with(
        debit_agent=agent,
        credit_agent=creditor,
        amount=500.0,
        memo=ANY,
        tick=10
    )
