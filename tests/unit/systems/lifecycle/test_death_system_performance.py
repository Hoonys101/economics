import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle.death_system import DeathSystem
from simulation.systems.lifecycle.api import DeathConfigDTO
from modules.finance.api import ILiquidatable
from typing import Protocol, runtime_checkable, Any, Dict, List

# Define lightweight protocols to replace heavy imports
@runtime_checkable
class IFirm(Protocol):
    id: int
    is_active: bool
    hr_state: Any
    def get_all_items(self) -> Dict[str, float]: ...

@runtime_checkable
class IHousehold(Protocol):
    id: int
    is_active: bool
    inventory: Dict[str, float]
    _econ_state: Any
    def get_all_items(self) -> Dict[str, float]: ...

class TestDeathSystemPerformance:
    @pytest.fixture
    def death_system(self):
        config = MagicMock(spec=DeathConfigDTO)
        config.default_fallback_price_pennies = 1000

        inheritance_manager = MagicMock()
        liquidation_manager = MagicMock()
        settlement_system = MagicMock()
        public_manager = MagicMock()
        logger = MagicMock()

        return DeathSystem(config, inheritance_manager, liquidation_manager, settlement_system, public_manager, logger)

    def test_localized_agent_removal(self, death_system):
        """
        Verifies that DeathSystem removes agents via localized deletion (O(1))
        instead of rebuilding the entire agents dictionary (O(N)).
        """
        # Setup active firm
        active_firm = MagicMock(spec=IFirm)
        active_firm.is_active = True
        active_firm.id = 1

        # Setup dead firm
        dead_firm = MagicMock(spec=IFirm)
        dead_firm.is_active = False
        dead_firm.id = 2
        dead_firm.get_all_items = MagicMock(return_value={})
        dead_firm.hr_state = MagicMock()
        dead_firm.hr_state.employees = []

        # Setup active household
        active_hh = MagicMock(spec=IHousehold)
        active_hh.is_active = True
        active_hh.id = 101

        # Setup dead household
        dead_hh = MagicMock(spec=IHousehold)
        dead_hh.is_active = False
        dead_hh.id = 102
        dead_hh.get_all_items = MagicMock(return_value={})
        dead_hh._econ_state = MagicMock()
        dead_hh._econ_state.inventory = {}
        dead_hh.inventory = {} # Fallback

        # Setup "Ghost" agent (e.g. System Agent or just noise)
        ghost_agent = MagicMock()
        ghost_agent.id = 999

        state = MagicMock()
        state.firms = [active_firm, dead_firm]
        state.households = [active_hh, dead_hh]
        state.agents = {
            1: active_firm,
            2: dead_firm,
            101: active_hh,
            102: dead_hh,
            999: ghost_agent # Should preserve if NOT rebuilding
        }
        state.time = 1
        state.markets = {}
        state.inactive_agents = {}
        state.government = None
        state.currency_registry_handler = None
        state.currency_holders = None

        # Mock settlement system interaction
        death_system.settlement_system.get_agent_banks.return_value = []

        # Execute
        death_system.execute(state)

        # Assertions
        assert 1 in state.agents
        assert 101 in state.agents
        assert 2 not in state.agents
        assert 102 not in state.agents

        # KEY ASSERTION: Ghost agent must remain if we are NOT rebuilding
        assert 999 in state.agents, "Optimization Failed: state.agents was rebuilt, removing the Ghost agent."

        # Verify list updates
        assert active_firm in state.firms
        assert dead_firm not in state.firms
        assert active_hh in state.households
        assert dead_hh not in state.households
