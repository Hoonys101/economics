import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.registries.estate_registry import EstateRegistry
from modules.simulation.api import IAgent
from modules.finance.api import IFinancialEntity, IFinancialAgent
from modules.system.constants import ID_PUBLIC_MANAGER

class TestEstateRegistry:

    def test_process_estate_distribution_to_heir(self):
        registry = EstateRegistry()
        mock_settlement_system = MagicMock()

        # Setup Dead Agent with Balance and Heir
        dead_agent = MagicMock(spec=IFinancialEntity)
        dead_agent.id = 666
        # Need balance_pennies for IFinancialEntity
        type(dead_agent).balance_pennies = PropertyMock(return_value=500)
        dead_agent.children_ids = [777] # Heir ID
        registry.add_to_estate(dead_agent)

        # Setup Heir Agent in Registry
        heir_agent = MagicMock(spec=IFinancialAgent)
        heir_agent.id = 777
        mock_settlement_system.agent_registry.get_agent.side_effect = lambda uid: heir_agent if uid == 777 else None

        # Execute Distribution
        registry.process_estate_distribution(dead_agent, mock_settlement_system)

        # Verify Transfer to Heir
        mock_settlement_system.transfer.assert_called_once()
        args, kwargs = mock_settlement_system.transfer.call_args
        assert kwargs['debit_agent'] == dead_agent
        assert kwargs['credit_agent'] == heir_agent
        assert kwargs['amount'] == 500
        assert kwargs['memo'] == "inheritance_distribution"

    def test_process_estate_distribution_escheatment_fallback(self):
        registry = EstateRegistry()
        mock_settlement_system = MagicMock()

        # Setup Dead Agent with Balance but NO Heir
        dead_agent = MagicMock(spec=IFinancialAgent)
        dead_agent.id = 666
        type(dead_agent).balance_pennies = PropertyMock(return_value=999)
        dead_agent.children_ids = [] # No Heirs
        registry.add_to_estate(dead_agent)

        # Setup Government/PublicManager
        gov_agent = MagicMock(spec=IFinancialAgent)
        gov_agent.id = ID_PUBLIC_MANAGER
        mock_settlement_system.agent_registry.get_agent.side_effect = lambda uid: gov_agent if uid == ID_PUBLIC_MANAGER else None

        # Execute Distribution
        registry.process_estate_distribution(dead_agent, mock_settlement_system)

        # Verify Transfer to Government (Escheatment)
        mock_settlement_system.transfer.assert_called_once()
        args, kwargs = mock_settlement_system.transfer.call_args
        assert kwargs['debit_agent'] == dead_agent
        assert kwargs['credit_agent'] == gov_agent
        assert kwargs['amount'] == 999
        assert kwargs['memo'] == "escheatment"
