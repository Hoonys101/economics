import pytest
from unittest.mock import MagicMock, Mock, ANY
from simulation.initialization.initializer import SimulationInitializer
from simulation.engine import Simulation
from simulation.systems.bootstrapper import Bootstrapper
from modules.system.constants import ID_BANK
from modules.simulation.api import AgentID
from modules.system.api import DEFAULT_CURRENCY
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.systems.demographic_manager import DemographicManager

class TestGhostFirmPrevention:

    @pytest.fixture
    def mock_sim(self):
        sim = MagicMock(spec=Simulation)
        sim.agents = {}
        sim.households = []
        sim.firms = []
        sim.agent_registry = MagicMock()
        sim.settlement_system = MagicMock()
        sim.bank = MagicMock()
        sim.bank.id = AgentID(ID_BANK)
        sim.world_state = MagicMock()
        sim.world_state.agents = sim.agents

        # WO-WAVE-B-4-TEST: Fix regression by initializing demographic_manager
        sim.demographic_manager = MagicMock(spec=DemographicManager)

        return sim

    def test_init_phase4_population_registers_agents_atomically(self, mock_sim):
        # Setup
        initializer = SimulationInitializer(
            config_manager=MagicMock(),
            config_module=MagicMock(),
            goods_data=[],
            repository=MagicMock(),
            logger=MagicMock(),
            households=[],
            firms=[],
            ai_trainer=MagicMock()
        )

        hh = MagicMock(spec=Household)
        hh.id = 101
        firm = MagicMock(spec=Firm)
        firm.id = 201

        mock_sim.households = [hh]
        mock_sim.firms = [firm]
        # FIX: update initializer attributes because _init_phase4_population uses them
        initializer.households = [hh]
        initializer.firms = [firm]

        mock_sim.agents = {} # Initially empty or None

        # WO-WAVE-B-4-TEST: demographic_manager is now mocked in fixture

        # Execute
        initializer._init_phase4_population(mock_sim)

        # Verify Household
        assert 101 in mock_sim.agents
        mock_sim.agent_registry.register.assert_any_call(hh)
        mock_sim.settlement_system.register_account.assert_any_call(ID_BANK, 101)
        assert hh.settlement_system == mock_sim.settlement_system

        # Verify Firm
        assert 201 in mock_sim.agents
        mock_sim.agent_registry.register.assert_any_call(firm)
        mock_sim.settlement_system.register_account.assert_any_call(ID_BANK, 201)
        assert firm.settlement_system == mock_sim.settlement_system

    def test_bootstrapper_raises_key_error_on_unregistered_agent(self):
        # Setup
        central_bank = MagicMock()
        firm = MagicMock(spec=Firm)
        firm.id = 301
        firm.wallet = MagicMock()
        firm.wallet.get_balance.return_value = 0
        settlement_system = MagicMock()

        # Mock transfer to return None (failure)
        settlement_system.transfer.return_value = None

        config = MagicMock()

        # Execute & Verify
        with pytest.raises(KeyError, match="Agent possibly not registered"):
            Bootstrapper.inject_liquidity_for_firm(
                firm=firm,
                config=config,
                settlement_system=settlement_system,
                central_bank=central_bank,
                current_tick=0
            )

    def test_bootstrapper_raises_key_error_on_distribute_wealth_failure(self):
        # Setup
        central_bank = MagicMock()
        agent = MagicMock() # Could be any agent, using generic
        agent.id = 401
        settlement_system = MagicMock()

        # Mock transfer to return None (failure)
        settlement_system.transfer.return_value = None

        # Execute & Verify
        with pytest.raises(KeyError, match="Agent possibly not registered"):
            Bootstrapper.distribute_initial_wealth(
                central_bank=central_bank,
                target_agent=agent,
                amount=1000,
                settlement_system=settlement_system
            )
