import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem

def test_settlement_to_unregistered_agent_handling():
    """
    Regression Test for TD-FORENSIC-003.
    Simulates sending funds to an agent ID that exists in Registry but not in Engine cache.
    """
    # 1. Setup
    registry = MagicMock()
    # Agent 999 exists in registry
    mock_agent = MagicMock(id=999, balance_pennies=0)
    registry.get_agent.return_value = mock_agent
    
    system = SettlementSystem(agent_registry=registry, logger=MagicMock())
    
    # Mock source agent
    source_agent = MagicMock(id=1)
    source_agent.balance_pennies = 1000
    
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
