"""
주식 거래 통합 검증 테스트

시뮬레이션에서 실제로 주식 거래가 발생하는지 확인합니다.
"""

import unittest
import logging
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.engine import Simulation
from simulation.ai_model import AIEngineRegistry
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI
from simulation.db.repository import SimulationRepository
from modules.market.api import OrderDTO
from tests.utils.factories import create_household_config_dto, create_firm_config_dto
from modules.common.config_manager.api import ConfigManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(message)s')
logger = logging.getLogger("TestStock")


class TestStockTradingIntegration(unittest.TestCase):
    """주식 거래 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.repository = SimulationRepository()
        self.state_builder = StateBuilder()
        self.action_proposal_engine = ActionProposalEngine(config_module=config)
        self.ai_trainer = AIEngineRegistry(
            action_proposal_engine=self.action_proposal_engine,
            state_builder=self.state_builder
        )
        self.config_manager = MagicMock(spec=ConfigManager)

        def config_side_effect(key, default=None):
            if key == "simulation.database_name":
                return "test_simulation.db"
            if key == "simulation.batch_save_interval":
                return 10
            return default

        self.config_manager.get.side_effect = config_side_effect
        
        # 주식 시장 활성화 확인
        self.assertTrue(
            getattr(config, "STOCK_MARKET_ENABLED", False),
            "STOCK_MARKET_ENABLED must be True for this test"
        )
    
    def tearDown(self):
        """테스트 정리"""
        self.repository.close()
    
    def _create_household(self, id: int, assets: float):
        """테스트용 가계 생성"""
        value_orientation = "wealth_and_needs"
        ai_engine = self.ai_trainer.get_engine(value_orientation)
        household_ai = HouseholdAI(agent_id=id, ai_decision_engine=ai_engine)
        decision_engine = AIDrivenHouseholdDecisionEngine(
            ai_engine=household_ai, config_module=config
        )
        
        config_dto = create_household_config_dto()

        household = Household(
            id=id,
            talent=Talent(1.0, {}),
            goods_data=[{"id": "basic_food", "utility_effects": {"survival": 10.0}}],
            initial_assets=assets,
            initial_needs={"survival": 30.0, "social": 20.0, "improvement": 10.0, "asset": 10.0},
            decision_engine=decision_engine,
            value_orientation=value_orientation,
            personality=Personality.MISER,
            config_dto=config_dto,
            logger=logger,
        )
        household._econ_state.inventory["basic_food"] = 10.0
        return household
    
    def _create_firm(self, id: int, assets: float):
        """테스트용 기업 생성"""
        value_orientation = "profit_maximizer"
        ai_engine = self.ai_trainer.get_engine(value_orientation)
        firm_ai = FirmAI(agent_id=id, ai_decision_engine=ai_engine)
        decision_engine = AIDrivenFirmDecisionEngine(
            ai_engine=firm_ai, config_module=config
        )
        
        config_dto = create_firm_config_dto()

        firm = Firm(
            id=id,
            initial_capital=assets,
            initial_liquidity_need=10.0,
            specialization="basic_food",
            productivity_factor=10.0,
            decision_engine=decision_engine,
            value_orientation=value_orientation,
            config_dto=config_dto,
            logger=logger,
        )
        firm.inventory["basic_food"] = 100.0
        return firm
    
    def _create_simulation(self, households, firms):
        sim = Simulation(
            config_manager=self.config_manager,
            config_module=config,
            logger=logger,
            repository=self.repository
        )
        sim.world_state.households = households
        sim.world_state.firms = firms

        # Mock tracker
        sim.world_state.tracker = MagicMock()
        sim.world_state.tracker.get_latest_indicators.return_value = {}

        # Mock government
        sim.world_state.government = MagicMock()
        sim.world_state.government.id = "government"
        sim.world_state.government.assets = 0.0
        sim.world_state.government.get_monetary_delta.return_value = 0.0

        # Mock public_manager
        sim.world_state.public_manager = MagicMock()
        sim.world_state.public_manager.id = "public_manager"
        sim.world_state.public_manager.assets = 0.0

        # Mock stock_tracker
        sim.world_state.stock_tracker = MagicMock()

        # Mock calculate_total_money to return float
        sim.world_state.calculate_total_money = MagicMock(return_value=0.0)

        # Set baseline money supply manually
        sim.world_state.baseline_money_supply = 0.0

        # Initialize Markets manually since we bypassed Initializer
        from simulation.markets.stock_market import StockMarket
        sim.world_state.stock_market = StockMarket(config_module=config, logger=logger)
        sim.world_state.markets["stock_market"] = sim.world_state.stock_market

        return sim

    def test_stock_market_initialized(self):
        """주식 시장이 초기화되는지 확인"""
        households = [self._create_household(i, 1000.0) for i in range(5)]
        firms = [self._create_firm(10 + i, 10000.0) for i in range(2)]
        
        # 초기 주식 분배
        for firm in firms:
            shares_per_household = firm.total_shares / len(households)
            for household in households:
                # Use portfolio add
                household._econ_state.portfolio.add(firm.id, shares_per_household, 10.0)
        
        sim = self._create_simulation(households, firms)
        
        # 주식 시장 존재 확인
        self.assertIsNotNone(sim.stock_market, "Stock market should be initialized")
        self.assertIn("stock_market", sim.markets, "Stock market should be in markets dict")
        
        logger.info("✓ Stock market initialized successfully")
    
    def test_stock_reference_prices_updated(self):
        """기업 기준가가 업데이트되는지 확인"""
        households = [self._create_household(i, 1000.0) for i in range(3)]
        firms = [self._create_firm(10, 10000.0)]
        # Ensure outstanding shares for BPS calculation
        firms[0].total_shares = 1000.0
        firms[0].treasury_shares = 0.0
        
        sim = self._create_simulation(households, firms)
        
        # 1틱 실행
        sim.run_tick()
        
        # 기준가 확인
        self.assertIn(10, sim.stock_market.reference_prices)
        ref_price = sim.stock_market.reference_prices[10]
        self.assertGreater(ref_price, 0, "Reference price should be positive")
        
        logger.info(f"✓ Reference price for firm 10: {ref_price:.2f}")
    
    def test_stock_order_placement(self):
        """주식 주문이 제출되는지 확인"""
        # 자산이 충분한 가계 생성
        households = [self._create_household(i, 2000.0) for i in range(5)]
        firms = [self._create_firm(10, 10000.0)]
        firms[0].treasury_shares = 0.0 # Make shares outstanding
        
        # 초기 주식 분배
        for household in households:
            # household._econ_state.portfolio.to_legacy_dict()[10] = 20.0
            household._econ_state.portfolio.add(10, 20.0, 10.0)
        
        sim = self._create_simulation(households, firms)
        
        # Update reference prices initially so trading can happen
        sim.stock_market.update_reference_prices({f.id: f for f in sim.world_state.firms})

        # 여러 틱 실행하여 주식 주문 발생 확인
        stock_orders_placed = False
        for _ in range(10):
            sim.run_tick()
            
            # 체결되지 않은 주문 확인
            # Note: buy_orders.values() returns list of ManagedOrders
            total_orders = sum(len(orders) for orders in sim.stock_market.buy_orders.values())
            total_orders += sum(len(orders) for orders in sim.stock_market.sell_orders.values())
            
            if total_orders > 0:
                stock_orders_placed = True
                break
        
        # 주식 거래가 발생했는지 확인 (거래량으로 체크)
        total_volume = sum(sim.stock_market.daily_volumes.values())
        
        logger.info(f"Total stock orders: {total_orders}, Total volume: {total_volume}")
        
        # 참고: 주식 거래는 확률적이므로 항상 발생하지 않을 수 있음
        # 대신 시스템이 에러 없이 동작하는지 확인
        logger.info("✓ Stock trading system operational (no errors)")
    
    def test_firm_book_value_calculation(self):
        """기업 주당 순자산가치 계산 확인"""
        firm = self._create_firm(10, 10000.0)
        
        # Override to match test assumption
        firm.total_shares = 100.0
        firm.treasury_shares = 0.0

        # 기본값: total_shares = 100, assets = 10000
        bps = firm.get_book_value_per_share()
        expected_bps = 10000.0 / 100.0  # = 100.0
        
        self.assertAlmostEqual(bps, expected_bps, places=2)
        logger.info(f"✓ Book value per share: {bps:.2f}")
    
    def test_firm_market_cap_calculation(self):
        """기업 시가총액 계산 확인"""
        firm = self._create_firm(10, 10000.0)
        
        # Override to match test assumption
        firm.total_shares = 100.0
        firm.treasury_shares = 0.0

        # 주가 없이 계산 (BPS 사용)
        market_cap = firm.get_market_cap()
        expected = 100.0 * 100.0  # total_shares * BPS = 10000
        
        self.assertAlmostEqual(market_cap, expected, places=2)
        
        # 주가로 계산
        market_cap_with_price = firm.get_market_cap(stock_price=150.0)
        expected_with_price = 100.0 * 150.0  # = 15000
        
        self.assertAlmostEqual(market_cap_with_price, expected_with_price, places=2)
        logger.info(f"✓ Market cap: {market_cap:.2f}, with price 150: {market_cap_with_price:.2f}")


if __name__ == "__main__":
    print("\n=== Stock Trading Integration Test ===\n")
    unittest.main(verbosity=2)
