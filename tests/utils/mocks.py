import logging
from unittest.mock import MagicMock
from typing import Any, List, Dict, Optional
from modules.simulation.api import IBirthContext, IFinanceTickContext, IAgentRegistry
from modules.finance.api import IMonetaryAuthority, ICentralBank, IBank, IMonetaryLedger
from modules.finance.kernel.api import ISagaOrchestrator
from modules.system.constants import ID_BANK

class MockBirthContext(MagicMock):
    """
    Protocol-compliant Mock for IBirthContext.
    Provides standard defaults for agent registration and simulation environment.
    """
    def __init__(self, **kwargs):
        super().__init__(spec=IBirthContext, **kwargs)
        self.next_agent_id = kwargs.get('next_agent_id', 1000)
        self.agent_registry = kwargs.get('agent_registry', MagicMock(spec=IAgentRegistry))
        self.logger = kwargs.get('logger', MagicMock(spec=logging.Logger))
        self.households = kwargs.get('households', [])
        # Protocol fields required for IAgentRegistry integration
        self.currency_registry_handler = kwargs.get('currency_registry_handler', MagicMock(spec=IAgentRegistry))
        self.currency_holders = kwargs.get('currency_holders', [])
        # Registry and environment
        self.goods_data = kwargs.get('goods_data', {})
        self.bank = kwargs.get('bank', MagicMock(spec=IBank))

class MockFinanceTickContext(MagicMock):
    """
    Protocol-compliant Mock for IFinanceTickContext.
    Provides standard defaults for banking and monetary operations.
    """
    def __init__(self, **kwargs):
        super().__init__(spec=IFinanceTickContext, **kwargs)
        self.current_time = kwargs.get('current_time', 0)
        self.settlement_system = kwargs.get('settlement_system', MagicMock(spec=IMonetaryAuthority))
        self.central_bank = kwargs.get('central_bank', MagicMock(spec=ICentralBank))
        self.monetary_ledger = kwargs.get('monetary_ledger', MagicMock(spec=IMonetaryLedger))
        self.bank = kwargs.get('bank', MagicMock(spec=IBank))
        self.saga_orchestrator = kwargs.get('saga_orchestrator', MagicMock(spec=ISagaOrchestrator))
