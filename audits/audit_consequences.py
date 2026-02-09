import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from modules.system.event_bus.event_bus import EventBus
from modules.governance.judicial.system import JudicialSystem
from modules.events.dtos import LoanDefaultedEvent
from modules.simulation.api import IEducated
from modules.finance.api import ICreditFrozen

class MockAuditAgent:
    def __init__(self, id):
        self.id = id
        self.education_xp = 100.0
        self._credit_frozen_until_tick = 0
        self.assets = 1000.0
        self.wallet = MagicMock()
        self.wallet.get_balance.return_value = 1000.0

    @property
    def credit_frozen_until_tick(self):
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value):
        self._credit_frozen_until_tick = value

    def get_portfolio(self):
        m = MagicMock()
        m.assets = []
        return m

    def clear_portfolio(self): pass

def audit_judicial_system():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Audit")
    logger.info("Starting Audit: Judicial System Consequences")

    # Setup
    event_bus = EventBus()
    # Mock other dependencies
    settlement_system = MagicMock()
    agent_registry = MagicMock()
    shareholder_registry = MagicMock()
    config_manager = MagicMock()

    # Configure defaults
    # xp penalty 0.2, jail 100
    def config_get(key, default=None):
        if "xp_penalty" in key: return 0.2
        if "credit_recovery" in key: return 100
        return default
    config_manager.get.side_effect = config_get

    judicial_system = JudicialSystem(
        event_bus=event_bus,
        settlement_system=settlement_system,
        agent_registry=agent_registry,
        shareholder_registry=shareholder_registry,
        config_manager=config_manager
    )

    # Mock Agent
    agent = MockAuditAgent(1)
    creditor = MockAuditAgent(2)

    agent_registry.get_agent.side_effect = lambda aid: agent if aid == 1 else creditor

    # Record initial state
    initial_xp = agent.education_xp

    # Trigger Event
    event: LoanDefaultedEvent = {
        "event_type": "LOAN_DEFAULTED",
        "tick": 50,
        "agent_id": 1,
        "loan_id": "L1",
        "defaulted_amount": 100.0,
        "creditor_id": 2
    }

    logger.info("Publishing LoanDefaultedEvent...")
    event_bus.publish(event)

    # Verification
    errors = []

    # 1. Check XP Penalty
    expected_xp = initial_xp * (1.0 - 0.2)
    if abs(agent.education_xp - expected_xp) < 0.01:
        logger.info("SUCCESS: XP Penalty applied correctly.")
    else:
        msg = f"FAILURE: XP Penalty mismatch. Expected {expected_xp}, got {agent.education_xp}"
        logger.error(msg)
        errors.append(msg)

    # 2. Check Credit Freeze
    expected_unfreeze = 50 + 100
    if agent.credit_frozen_until_tick == expected_unfreeze:
        logger.info("SUCCESS: Credit Frozen correctly.")
    else:
        msg = f"FAILURE: Credit Freeze mismatch. Expected {expected_unfreeze}, got {agent.credit_frozen_until_tick}"
        logger.error(msg)
        errors.append(msg)

    # 3. Check Asset Seizure
    # Agent had 1000. Defaulted 100. JudicialSystem seizes all liquid assets (IFinancialEntity.assets).
    # MockAgent.assets = 1000.
    # SettlementSystem.transfer should be called with amount 1000.
    settlement_system.transfer.assert_called()
    call_args = settlement_system.transfer.call_args
    kwargs = call_args[1]
    if kwargs['amount'] == 1000.0 and kwargs['debit_agent'] == agent and kwargs['credit_agent'] == creditor:
        logger.info("SUCCESS: Asset Seizure command issued correctly.")
    else:
        msg = f"FAILURE: Asset Seizure mismatch. Args: {kwargs}"
        logger.error(msg)
        errors.append(msg)

    if errors:
        logger.error(f"Audit Failed with {len(errors)} errors.")
        sys.exit(1)

    logger.info("Audit Completed Successfully.")

if __name__ == "__main__":
    audit_judicial_system()
