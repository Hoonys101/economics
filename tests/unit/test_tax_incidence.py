import unittest
from unittest.mock import MagicMock
import logging
import sys
import os

# Ensure we can import from the root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI
from simulation.db.repository import SimulationRepository
from simulation.models import Order
import config as cfg
from tests.utils.factories import create_household_config_dto, create_firm_config_dto

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("TestTaxIncidence")

class TestTaxIncidence(unittest.TestCase):
    def setUp(self):
        self.repository = SimulationRepository()
        self.state_builder = StateBuilder()
        self.action_proposal_engine = ActionProposalEngine(config_module=cfg)
        self.ai_trainer = AIEngineRegistry(
            action_proposal_engine=self.action_proposal_engine,
            state_builder=self.state_builder
        )

    def tearDown(self):
        self.repository.close()

    def _create_household(self, id: int, assets: float):
        mock_de = MagicMock()
        return Household(
            id=id,
            talent=Talent(1.0, {}),
            goods_data=[],
            initial_assets=assets,
            initial_needs={},
            decision_engine=mock_de,
            value_orientation="wealth_and_needs",
            personality=Personality.MISER,
            config_dto=create_household_config_dto(),
            logger=logger,
        )

    def _create_firm(self, id: int, assets: float):
        mock_de = MagicMock()
        return Firm(
            id=id,
            initial_capital=assets,
            initial_liquidity_need=0.0,
            specialization="basic_food",
            productivity_factor=1.0,
            decision_engine=mock_de,
            value_orientation="profit_maximizer",
            config_dto=create_firm_config_dto(),
            logger=logger,
        )

    def _setup_simulation(self, h, f):
        # Mock ConfigManager
        mock_config_manager = MagicMock()
        mock_config_manager.get.return_value = "test.db"

        sim = Simulation(
            config_manager=mock_config_manager,
            config_module=cfg,
            logger=logger,
            repository=self.repository
        )
        sim.world_state.households = [h]
        sim.world_state.firms = [f]
        sim.world_state.agents = {1: h, 101: f}

        # Government
        from simulation.agents.government import Government
        gov = Government(id=999, config_module=cfg)
        sim.world_state.government = gov
        sim.world_state.agents[999] = gov

        # SettlementSystem
        from simulation.systems.settlement_system import SettlementSystem
        sim.settlement_system = SettlementSystem(logger=logger)
        h.settlement_system = sim.settlement_system
        f.settlement_system = sim.settlement_system
        gov.settlement_system = sim.settlement_system

        # TransactionManager components
        from simulation.systems.transaction_manager import TransactionManager
        from simulation.systems.registry import Registry
        from simulation.systems.accounting import AccountingSystem
        from simulation.systems.central_bank_system import CentralBankSystem

        sim.registry = Registry(logger=logger)
        sim.accounting_system = AccountingSystem(logger=logger)
        sim.central_bank = MagicMock() # Mock Central Bank
        sim.central_bank_system = CentralBankSystem(sim.central_bank, sim.settlement_system, logger)

        sim.world_state.transaction_processor = TransactionManager(
            registry=sim.registry,
            accounting_system=sim.accounting_system,
            settlement_system=sim.settlement_system,
            central_bank_system=sim.central_bank_system,
            config=cfg,
            handlers={},
            logger=logger
        )

        return sim

    def test_household_payer_scenario(self):
        """가계가 세금을 납부하는 경우 (원천징수)"""
        cfg.INCOME_TAX_PAYER = "HOUSEHOLD"
        h = self._create_household(1, 1000.0)
        f = self._create_firm(101, 5000.0)
        sim = self._setup_simulation(h, f)
        
        # 100원 매칭 (노동 거래)
        from simulation.models import Transaction
        tx = Transaction(buyer_id=101, seller_id=1, item_id="labor", quantity=1.0, price=100.0, market_id="labor", transaction_type="labor", time=1)
        sim._process_transactions([tx])
        
        # 가계: 1000 + (100 - 10) = 1090
        # 기업: 5000 - 100 = 4900
        self.assertEqual(h.assets, 1090.0)
        self.assertEqual(f.assets, 4900.0)
        self.assertEqual(sim.government.assets, 10.0)
        print("✓ Household Payer (Withholding): Agent Assets Correct")

    def test_firm_payer_scenario(self):
        """기업이 세금을 납부하는 경우 (추가 납부)"""
        cfg.INCOME_TAX_PAYER = "FIRM"
        h = self._create_household(1, 1000.0)
        f = self._create_firm(101, 5000.0)
        sim = self._setup_simulation(h, f)
        
        # 100원 매칭 (노동 거래)
        from simulation.models import Transaction
        tx = Transaction(buyer_id=101, seller_id=1, item_id="labor", quantity=1.0, price=100.0, market_id="labor", transaction_type="labor", time=1)
        sim._process_transactions([tx])
        
        # 가계: 1000 + 100 = 1100
        # 기업: 5000 - (100 + 10) = 4890
        self.assertEqual(h.assets, 1100.0)
        self.assertEqual(f.assets, 4890.0)
        self.assertEqual(sim.government.assets, 10.0)
        print("✓ Firm Payer (Extra Tax): Agent Assets Correct")

if __name__ == "__main__":
    unittest.main()
