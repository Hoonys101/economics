import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.registries.estate_registry import EstateRegistry
from modules.simulation.api import IAgent
from modules.finance.api import IFinancialEntity, IFinancialAgent
from modules.system.constants import ID_PUBLIC_MANAGER, ID_GOVERNMENT

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

        # Mock Transfer Success
        mock_settlement_system.transfer.return_value = MagicMock() # Successful transfer returns a TX

        # Execute Distribution with TICK
        current_tick = 123
        registry.process_estate_distribution(dead_agent, mock_settlement_system, tick=current_tick)

        # Verify Transfer to Heir includes TICK
        mock_settlement_system.transfer.assert_called_once()
        args, kwargs = mock_settlement_system.transfer.call_args
        assert kwargs['debit_agent'] == dead_agent
        assert kwargs['credit_agent'] == heir_agent
        assert kwargs['amount'] == 500
        assert kwargs['memo'] == "inheritance_distribution"
        assert kwargs['tick'] == current_tick

    def test_process_estate_distribution_escheatment_fallback(self):
        registry = EstateRegistry()
        mock_settlement_system = MagicMock()

        # Setup Dead Agent with Balance but NO Heir
        dead_agent = MagicMock(spec=IFinancialEntity)
        dead_agent.id = 666
        type(dead_agent).balance_pennies = PropertyMock(return_value=999)
        dead_agent.children_ids = [] # No Heirs
        registry.add_to_estate(dead_agent)

        # Setup Government/PublicManager
        gov_agent = MagicMock(spec=IFinancialAgent)
        gov_agent.id = ID_PUBLIC_MANAGER
        mock_settlement_system.agent_registry.get_agent.side_effect = lambda uid: gov_agent if uid == ID_PUBLIC_MANAGER else None

        # Mock Transfer Success
        mock_settlement_system.transfer.return_value = MagicMock()

        # Execute Distribution with TICK
        current_tick = 456
        registry.process_estate_distribution(dead_agent, mock_settlement_system, tick=current_tick)

        # Verify Transfer to Government (Escheatment) includes TICK
        mock_settlement_system.transfer.assert_called_once()
        args, kwargs = mock_settlement_system.transfer.call_args
        assert kwargs['debit_agent'] == dead_agent
        assert kwargs['credit_agent'] == gov_agent
        assert kwargs['amount'] == 999
        assert kwargs['memo'] == "escheatment"
        assert kwargs['tick'] == current_tick

    def test_escheatment_fallback_to_government_id(self):
        # Verify fallback to ID_GOVERNMENT if ID_PUBLIC_MANAGER is missing
        registry = EstateRegistry()
        mock_settlement_system = MagicMock()

        dead_agent = MagicMock(spec=IFinancialEntity)
        dead_agent.id = 666
        type(dead_agent).balance_pennies = PropertyMock(return_value=100)
        dead_agent.children_ids = []

        # Mock Registry: No Public Manager, only Government
        gov_agent = MagicMock(spec=IFinancialAgent)
        gov_agent.id = ID_GOVERNMENT

        def get_agent_side_effect(uid):
            if uid == ID_PUBLIC_MANAGER: return None
            if uid == ID_GOVERNMENT: return gov_agent
            return None

        mock_settlement_system.agent_registry.get_agent.side_effect = get_agent_side_effect
        mock_settlement_system.transfer.return_value = MagicMock()

        registry.process_estate_distribution(dead_agent, mock_settlement_system, tick=789)

        mock_settlement_system.transfer.assert_called_once()
        args, kwargs = mock_settlement_system.transfer.call_args
        assert kwargs['credit_agent'] == gov_agent
        assert kwargs['tick'] == 789

    def test_wealth_orphanage_fix_heir_transfer_fail_triggers_escheatment(self):
        registry = EstateRegistry()
        mock_settlement_system = MagicMock()

        # Setup Dead Agent with Balance and Heir
        dead_agent = MagicMock(spec=IFinancialEntity)
        dead_agent.id = 666
        type(dead_agent).balance_pennies = PropertyMock(return_value=500)
        dead_agent.children_ids = [777]
        registry.add_to_estate(dead_agent)

        # Setup Heir
        heir_agent = MagicMock(spec=IFinancialAgent)
        heir_agent.id = 777

        # Setup Gov
        gov_agent = MagicMock(spec=IFinancialAgent)
        gov_agent.id = ID_PUBLIC_MANAGER

        mock_settlement_system.agent_registry.get_agent.side_effect = lambda uid: heir_agent if uid == 777 else (gov_agent if uid == ID_PUBLIC_MANAGER else None)

        # Mock Heir Transfer FAILURE (returns None)
        # Mock Gov Transfer SUCCESS (returns Mock)
        def transfer_side_effect(**kwargs):
            if kwargs['credit_agent'] == heir_agent:
                return None
            if kwargs['credit_agent'] == gov_agent:
                return MagicMock()
            return None

        mock_settlement_system.transfer.side_effect = transfer_side_effect

        # Execute
        registry.process_estate_distribution(dead_agent, mock_settlement_system, tick=111)

        # Verify calls
        assert mock_settlement_system.transfer.call_count == 2

        # First call: Attempt to Heir
        call1 = mock_settlement_system.transfer.call_args_list[0]
        assert call1[1]['credit_agent'] == heir_agent

        # Second call: Fallback to Gov (Escheatment) because first failed
        call2 = mock_settlement_system.transfer.call_args_list[1]
        assert call2[1]['credit_agent'] == gov_agent
        assert call2[1]['memo'] == "escheatment"
