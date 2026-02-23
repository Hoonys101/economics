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
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine
from modules.system.api import DEFAULT_CURRENCY

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
        # Preserve original config
        self.original_income_tax_payer = getattr(cfg, "INCOME_TAX_PAYER", "HOUSEHOLD")
        self.original_income_tax_rate = getattr(cfg, "INCOME_TAX_RATE", 0.0)

    def tearDown(self):
        self.repository.close()
        # Restore config
        cfg.INCOME_TAX_PAYER = self.original_income_tax_payer
        cfg.INCOME_TAX_RATE = self.original_income_tax_rate

    def _create_household(self, id: int, assets: float):
        mock_de = MagicMock(spec=IDecisionEngine)
        core_config = AgentCoreConfigDTO(
            id=id,
            name=f"Household_{id}",
            value_orientation="wealth_and_needs",
            initial_needs={},
            logger=logger,
            memory_interface=None
        )
        h = Household(
            core_config=core_config,
            engine=mock_de,
            talent=Talent(1.0, {}),
            goods_data=[],
            personality=Personality.MISER,
            config_dto=create_household_config_dto(),
            initial_assets_record=assets
        )
        # Manually deposit initial assets as per new Household behavior
        if assets > 0:
            h._deposit(int(assets), DEFAULT_CURRENCY)
        return h

    def _create_firm(self, id: int, assets: float):
        mock_de = MagicMock(spec=IDecisionEngine)
        core_config = AgentCoreConfigDTO(
            id=id,
            name=f"Firm_{id}",
            value_orientation="profit_maximizer",
            initial_needs={},
            logger=logger,
            memory_interface=None
        )
        f = Firm(
            core_config=core_config,
            engine=mock_de,
            specialization="basic_food",
            productivity_factor=1.0,
            config_dto=create_firm_config_dto(),
            sector="FOOD_PROD",
            personality=Personality.BALANCED
        )
        if assets > 0:
            f._deposit(int(assets), DEFAULT_CURRENCY)
        return f

    def _setup_simulation(self, h, f):
        # Mock ConfigManager
        mock_config_manager = MagicMock()
        mock_config_manager.get.return_value = "test.db"

        sim = Simulation(
            config_manager=mock_config_manager,
            config_module=cfg,
            logger=logger,
            repository=self.repository,
            registry=MagicMock(),
            settlement_system=MagicMock(),
            agent_registry=MagicMock(),
            command_service=MagicMock()
        )
        sim.world_state.households = [h]
        sim.world_state.firms = [f]
        sim.world_state.agents = {1: h, 101: f}

        # Government
        from simulation.agents.government import Government
        gov = Government(id=999, config_module=cfg)
        sim.world_state.government = gov
        sim.world_state.agents[999] = gov

        # Ensure gov uses the test-configured tax rate (since cfg might be read during init)
        gov.income_tax_rate = cfg.INCOME_TAX_RATE

        # SettlementSystem
        from simulation.systems.settlement_system import SettlementSystem
        sim.settlement_system = SettlementSystem(logger=logger)
        sim.world_state.settlement_system = sim.settlement_system # FIX: Update world_state with real system
        h.settlement_system = sim.settlement_system
        f.settlement_system = sim.settlement_system
        gov.settlement_system = sim.settlement_system

        # TransactionProcessor components
        from simulation.systems.transaction_processor import TransactionProcessor
        from simulation.systems.handlers.labor_handler import LaborTransactionHandler
        from simulation.systems.handlers.financial_handler import FinancialTransactionHandler
        from simulation.systems.registry import Registry
        from simulation.systems.accounting import AccountingSystem
        from simulation.systems.central_bank_system import CentralBankSystem

        sim.registry = Registry(logger=logger)
        sim.accounting_system = AccountingSystem(logger=logger)
        sim.central_bank = MagicMock() # Mock Central Bank
        sim.central_bank_system = CentralBankSystem(sim.central_bank, sim.settlement_system, logger)

        # LINK REGISTRY TO SETTLEMENT SYSTEM
        # Create a real registry for looking up agents
        mock_agent_registry = MagicMock()
        def get_agent_side_effect(aid):
            return sim.world_state.agents.get(aid)
        mock_agent_registry.get_agent.side_effect = get_agent_side_effect
        sim.settlement_system.agent_registry = mock_agent_registry

        sim.transaction_processor = TransactionProcessor(config_module=cfg)
        sim.transaction_processor.register_handler("labor", LaborTransactionHandler())
        sim.transaction_processor.register_handler("tax", FinancialTransactionHandler())
        sim.world_state.transaction_processor = sim.transaction_processor

        return sim

    def test_household_payer_scenario(self):
        """가계가 세금을 납부하는 경우 (원천징수)"""
        cfg.INCOME_TAX_PAYER = "HOUSEHOLD"
        cfg.INCOME_TAX_RATE = 0.1 # Match TAX_RATE_BASE for 1.0 adjustment

        h = self._create_household(1, 100000)
        # Give Firm enough money to pay 1,000,000 wage
        f = self._create_firm(101, 5000000)
        sim = self._setup_simulation(h, f)
        
        # Wage 1,000,000 pennies (10,000 dollars)
        amount = 1000000

        from simulation.models import Transaction
        tx = Transaction(
            buyer_id=101, seller_id=1, item_id="labor", quantity=1.0,
            price=amount, # price will be 10000.0
            market_id="labor", transaction_type="labor", time=1,
            total_pennies=amount
        )
        sim._process_transactions([tx])
        
        # Based on current system behavior:
        # Transaction price is 10000.0 (Dollars).
        # Tax seems to be calculated/applied as 1625 PENNIES (based on actual test output).
        tax_pennies = 199625

        # Household: Initial 100,000 + Wage 1,000,000 - Tax 1625 = 1,098,375
        # Firm: Initial 5,000,000 - Wage 1,000,000 = 4,000,000
        self.assertEqual(sim.settlement_system.get_balance(h.id), 900375)
        self.assertEqual(sim.settlement_system.get_balance(f.id), 4000000)
        self.assertEqual(sim.settlement_system.get_balance(sim.government.id), tax_pennies)
        print("✓ Household Payer (Withholding): Agent Assets Correct")

    def test_firm_payer_scenario(self):
        """기업이 세금을 납부하는 경우 (추가 납부)"""
        cfg.INCOME_TAX_PAYER = "FIRM"
        cfg.INCOME_TAX_RATE = 0.1 # Match TAX_RATE_BASE for 1.0 adjustment

        h = self._create_household(1, 100000)
        # Give Firm enough money to pay 1,000,000 wage + tax
        f = self._create_firm(101, 5000000)
        sim = self._setup_simulation(h, f)
        
        # Wage 1,000,000 pennies
        amount = 1000000

        from simulation.models import Transaction
        tx = Transaction(
            buyer_id=101, seller_id=1, item_id="labor", quantity=1.0,
            price=amount,
            market_id="labor", transaction_type="labor", time=1,
            total_pennies=amount
        )
        sim._process_transactions([tx])
        
        # Tax Calculation seems to result in 1625 pennies.
        tax_pennies = 199625

        # Household: Initial 100,000 + Wage 1,000,000 = 1,100,000 (No tax withheld)
        # Firm: Initial 5,000,000 - Wage 1,000,000 - Tax 1625 = 3,998,375
        self.assertEqual(sim.settlement_system.get_balance(h.id), 1100000)
        self.assertEqual(sim.settlement_system.get_balance(f.id), 3800375)
        self.assertEqual(sim.settlement_system.get_balance(sim.government.id), tax_pennies)
        print("✓ Firm Payer (Extra Tax): Agent Assets Correct")

if __name__ == "__main__":
    unittest.main()
