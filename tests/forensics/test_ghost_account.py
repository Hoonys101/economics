import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialEntity

def test_settlement_to_unregistered_agent_handling():
    """
    Regression Test for TD-FORENSIC-003.
    Simulates sending funds to an agent ID that exists in Registry but not in Engine cache.
    """
    # 1. Setup
    registry = MagicMock()
    # Agent 999 exists in registry
    mock_agent = MagicMock(spec=IFinancialEntity)
    mock_agent.id = 999
    mock_agent.balance_pennies = 0
    
    # Mock source agent
    source_agent = MagicMock(spec=IFinancialEntity)
    source_agent.id = 1
    source_agent.balance_pennies = 1000

    def get_agent_side_effect(agent_id):
        if agent_id == 999:
            return mock_agent
        if agent_id == 1:
            return source_agent
        return None

    registry.get_agent.side_effect = get_agent_side_effect

    system = SettlementSystem(agent_registry=registry, logger=MagicMock())
    
    # 2. Execute Transfer to 999
    # This forces the system to look up 999 in registry before engine failure
    result = system.transfer(
        debit_agent=source_agent,
        credit_agent=mock_agent, # Target
        amount=100,
        memo="startup_capital",
        tick=1
    )
    
    # 3. Assert
    assert result is not None, "Settlement should succeed by dynamically resolving agent from registry"
