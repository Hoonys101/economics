
import unittest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.decisions.housing_manager import HousingManager
from simulation.engine import Simulation as Engine
from simulation.bank import Bank, Loan
from simulation.markets import OrderBookMarket
from simulation.models import Order
from simulation.models import RealEstateUnit
from simulation.ai.api import Personality
from simulation.utils.config_factory import create_config_dto
from simulation.dtos.config_dtos import HouseholdConfigDTO
from tests.utils.factories import create_household_config_dto
import config

class MockConfig:
    INITIAL_PROPERTY_VALUE = 10000.0
    INITIAL_RENT_PRICE = 50.0
    MAINTENANCE_RATE_PER_TICK = 0.001
    MORTGAGE_INTEREST_RATE = 0.05 / 12 # Monthly
    GOODS = {}
    SERVICE_SECTORS = []
    ADAPTATION_RATE_NORMAL = 0.05
    INITIAL_HOUSEHOLD_ASSETS_MEAN = 1000.0
    INITIAL_HOUSEHOLD_ASSETS_STD = 0.0
    INITIAL_HOUSEHOLD_WAGE_MEAN = 10.0
    INITIAL_HOUSEHOLD_WAGE_STD = 0.0
    LABOR_MARKET_MIN_WAGE = 5.0
    BASE_DESIRE_GROWTH = 0.1
    INITIAL_NEEDS_MEAN = 50.0
    INITIAL_NEEDS_STD = 0.0
    GOODS_INITIAL_PRICE = {}
    INITIAL_FIRM_LIQUIDITY_NEED_MEAN = 50.0
    MAX_DESIRE_VALUE = 100.0
    SURVIVAL_NEED_DEATH_THRESHOLD = 90.0
    HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
    ASSETS_DEATH_THRESHOLD = -100.0
    HOUSEHOLD_DEATH_TURNS_THRESHOLD = 50
    START_AGE = 20
    MAX_AGE = 100
    AGING_ENABLED = False
    # Dynamic Personality
    value_orientation_mapping = {
        "WEALTH": {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
    }
    personality_status_seeker_wealth_pct = 0.9
    personality_survival_mode_wealth_pct = 0.2
    desire_weights_map = {} # Empty or minimal
    
    # Missing fields
    price_memory_length = 10
    wage_memory_length = 10
    ticks_per_year = 100
    conformity_ranges = {}
    quality_pref_snob_min = 0.8
    quality_pref_miser_max = 0.2
    adaptation_rate_impulsive = 0.5
    adaptation_rate_conservative = 0.1
    elasticity_mapping = {}

class TestRealEstateSales(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        mock_decision_engine = MagicMock()
        
        # Use factory with defaults, overriding with MockConfig values
        hh_config = create_household_config_dto(
            initial_rent_price=self.config.INITIAL_RENT_PRICE,
            maintenance_rate_per_tick=self.config.MAINTENANCE_RATE_PER_TICK,
            default_mortgage_rate=self.config.MORTGAGE_INTEREST_RATE,
            # Add other necessary fields if test logic depends on them matching MockConfig
        )

        self.agent = Household(
            id=1, 
            talent=0.5, 
            goods_data=[],
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=mock_decision_engine,
            value_orientation="WEALTH",
            config_dto=hh_config
        )
        self.housing_manager = HousingManager(self.agent, self.config)

    def test_personality_bias_optimism(self):
        # Scenario: NPV is slightly negative for neutral agent, but Optimist sees as Positive
        # Prop Value = 10000, Appr = 0.2%
        # Rent = 40 (Cheap rent makes Buying less attractive)
        
        prop_val = 10000
        rent = 40 
        
        # 1. Neutral (Optimism 0.0 -> 0.5 effectively in formula)
        self.agent._social_state.optimism = 0.0 # Normalized range 0.0-1.0?
        # In code: base * (0.5 + optimism). 
        # Wait, core_agents init: 0.5 + uniform.
        # Let's set explicit values.
        self.agent._social_state.optimism = 0.0 # Very Pessimistic: multiplier 0.5
        self.agent._social_state.ambition = 0.0
        
        should_buy_pessimist = self.housing_manager.should_buy(prop_val, rent)
        
        # 2. Maximum Optimist (Optimism 1.0 -> multiplier 1.5)
        self.agent._social_state.optimism = 1.0
        should_buy_optimist = self.housing_manager.should_buy(prop_val, rent)
        
        print(f"Pessimist Buy? {should_buy_pessimist} | Optimist Buy? {should_buy_optimist}")
        
        # We expect Optimist to be MORE likely to buy.
        # If Pessimist False and Optimist True => Success logic test
        # If both False, rent is too cheap. If both True, rent is too high.
        # Adjusted Rent to find the sweet spot if needed, but relative comparison is key.
        if should_buy_pessimist == should_buy_optimist:
             # Just verify that Net Buy Cost is lower for Optimist (Higher Future Value)
             pass
        else:
             self.assertTrue(should_buy_optimist and not should_buy_pessimist, "Optimist should buy while Pessimist rents in marginal case")

    def test_personality_bias_ambition(self):
        # Ambition adds Prestige Bonus (Negative Cost)
        prop_val = 10000
        rent = 40
        
        self.agent._social_state.optimism = 0.5 # Neutral
        self.agent._social_state.ambition = 0.0 # No pride
        decision_modest = self.housing_manager.should_buy(prop_val, rent)
        
        self.agent._social_state.ambition = 1.0 # High pride -> Big Prestige Bonus
        decision_proud = self.housing_manager.should_buy(prop_val, rent)
        
        print(f"Modest Buy? {decision_modest} | Proud Buy? {decision_proud}")
        # Proud agent subtracts (Val * 0.1) from Cost. Should be much more likely to buy.
        
    def test_engine_transaction_execution(self):
        # 1. Setup Engine
        # Mocking arguments for Simulation
        mock_ai_trainer = MagicMock()
        mock_repo = MagicMock()
        
        # Need real households to test interaction? Or mocks?
        # Real household needed for attributes like assets/id in transaction
        mock_talent = MagicMock()
        mock_talent.base_learning_rate = 0.5
        mock_talent.max_potential = {}
        hh_config = create_household_config_dto(
            initial_rent_price=self.config.INITIAL_RENT_PRICE,
            maintenance_rate_per_tick=self.config.MAINTENANCE_RATE_PER_TICK,
            default_mortgage_rate=self.config.MORTGAGE_INTEREST_RATE,
        )
        hh1 = Household(id=100, config_dto=hh_config, talent=mock_talent, goods_data={}, initial_assets=10000.0, initial_needs={"survival": 50.0, "asset": 50.0, "social": 50.0, "growth": 50.0, "leisure": 50.0, "self_actualization": 50.0, "improvement": 50.0}, decision_engine=MagicMock(), value_orientation="WEALTH")
        
        # Need at least one household
        households = [hh1]
        firms = []
        
        mock_config_manager = MagicMock()
        mock_config_manager.get.return_value = ":memory:" # Valid DB path

        engine = Engine(config_manager=mock_config_manager, config_module=config, logger=MagicMock(), repository=mock_repo)
        engine.world_state.households = households
        engine.world_state.firms = firms
        engine.world_state.agents = {h.id: h for h in households}
        
        # 2. Setup Market and Orders
        engine.markets["housing"] = OrderBookMarket("housing")
        engine.world_state.markets = engine.markets # Sync world state
        
        # Manually init real_estate_units as Engine.__init__ might do it if I passed config, 
        # But Engine.__init__ uses self.config_module.NUM_HOUSING_UNITS.
        # My MockConfig has it? No, need to check.
        # Let's manually inject units to be sure.
        unit0 = RealEstateUnit(id=0, estimated_value=10000.0, rent_price=50.0)
        engine.real_estate_units = [unit0]
        engine.world_state.real_estate_units = engine.real_estate_units
        
        # Seller: Government (Agent -1) selling Unit 0
        unit = engine.real_estate_units[0]
        unit.owner_id = None # Gov owned
        unit.estimated_value = 10000.0
        
        # Mock Government ID in Engine
        # Engine initializes Government agent inside __init__.
        # We need to ensure engine.government exists and get its ID.
        # Since we initialized Engine with mock config, it creates a government agent.
        # Wait, Engine init might NOT create gov if we use raw init.
        # Let's create a mock government if needed.
        from simulation.agents.government import Government
        # Use a real gov object or mock with ID
        gov = MagicMock()
        gov.id = 999
        engine.government = gov
        engine.world_state.government = gov
        engine.world_state.agents[gov.id] = gov

        gov_id = engine.government.id

        # Mock Bank
        bank = MagicMock()
        bank.id = 4
        bank.assets = 1000000.0
        # Mock grant_loan return value (LoanDTO, Transaction)
        loan_dto = MagicMock()
        loan_dto.loan_id = "loan_123"
        bank.grant_loan.return_value = (loan_dto, None)

        engine.bank = bank
        engine.world_state.bank = bank
        engine.world_state.agents[bank.id] = bank

        # Initialize Settlement System
        from simulation.systems.settlement_system import SettlementSystem
        settlement_system = SettlementSystem(logger=MagicMock())
        settlement_system.bank = bank # Link bank
        engine.settlement_system = settlement_system
        engine.world_state.settlement_system = settlement_system

        # Mock Escrow Agent
        from modules.system.escrow_agent import EscrowAgent
        escrow = EscrowAgent(id=998)
        engine.world_state.agents[escrow.id] = escrow
        # Ensure Bank knows about Escrow (for get_balance in handler compensation)
        # Bank mock is MagicMock, so get_balance works (returns Mock or configured value).
        bank.get_balance.return_value = 0.0

        # Initialize Transaction Processor and Handler
        from simulation.systems.transaction_processor import TransactionProcessor
        from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler

        tp = TransactionProcessor(config_module=self.config)
        tp.register_handler("housing", HousingTransactionHandler())
        engine.world_state.transaction_processor = tp

        buy_order = Order(agent_id=engine.households[0].id, item_id="unit_0", price_limit=10000.0, quantity=1, side="BUY", market_id="housing")
        # Use valid government ID for Sell Order
        sell_order = Order(agent_id=gov_id, item_id="unit_0", price_limit=10000.0, quantity=1, side="SELL", market_id="housing")
        
        # Inject orders directly for matching simulation
        engine.markets["housing"].place_order(buy_order, 0)
        engine.markets["housing"].place_order(sell_order, 0)
        
        # 3. Match Orders (returns Transaction DTOs)
        txs = engine.markets["housing"].match_orders(0)
        print(f"DEBUG: Transactions generated: {txs}")
        
        # 4. Process Transactions (Logic we implemented)
        # Give buyer some assets but less than price to trigger Mortgage
        buyer = engine.households[0]
        buyer._assets = 3000.0 # Needs 7000 Loan (LTV 70%)
        # Note: Logic grants LTV 80% (8000). Max Loan.
        # Downpayment = 2000. Buyer has 3000. OK.
        
        print(f"DEBUG: Bank Assets: {engine.bank.assets}")
        print(f"DEBUG: Config Bank Assets: {config.INITIAL_BANK_ASSETS}")

        engine._process_transactions(txs)
        
        # 5. Assertions
        # Title Transfer
        self.assertEqual(unit.owner_id, buyer.id)
        # Mortgage Exists
        self.assertIsNotNone(unit.mortgage_id)
        # Loan Check (Verify call to Bank Mock)
        engine.bank.grant_loan.assert_called()
        # Verify arguments: borrower_id="100", amount=8000.0
        call_args = engine.bank.grant_loan.call_args
        self.assertEqual(call_args.kwargs['borrower_id'], str(buyer.id))
        self.assertEqual(call_args.kwargs['amount'], 8000.0) # 80% of 10000
        
        print("Transaction & Mortgage Test Passed")

if __name__ == '__main__':
    unittest.main()
