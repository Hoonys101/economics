import sqlite3
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
import json

from simulation.db.database import get_db_connection, close_db_connection
from simulation.db.agent_repository import AgentRepository
from simulation.db.market_repository import MarketRepository
from simulation.db.analytics_repository import AnalyticsRepository
from simulation.db.run_repository import RunRepository

if TYPE_CHECKING:
    from simulation.dtos import (
        TransactionData,
        AgentStateData,
        MarketHistoryData,
        EconomicIndicatorData,
        AIDecisionData,
    )

logger = logging.getLogger(__name__)


class SimulationRepository:
    """
    Unit of Work container for simulation repositories.
    Provides access to domain-specific repositories sharing the same database connection.
    """

    def __init__(self):
        self.conn = get_db_connection()

        # Initialize sub-repositories sharing the same connection
        self.agents = AgentRepository(self.conn)
        self.markets = MarketRepository(self.conn)
        self.analytics = AnalyticsRepository(self.conn)
        self.runs = RunRepository(self.conn)

    def clear_all_data(self):
        """
        모든 시뮬레이션 관련 테이블의 데이터를 삭제합니다.
        """
        try:
            self.markets.clear_data()
            self.agents.clear_data()
            self.analytics.clear_data()
            
            # Reclaim disk space
            self.conn.execute("VACUUM")
            logger.info("All simulation data cleared and VACUUMed database.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing data: {e}")
            self.conn.rollback()

    def close(self):
        """
        Repository 사용을 마칠 때 데이터베이스 연결을 닫습니다.
        """
        close_db_connection()


if __name__ == "__main__":
    from simulation.dtos import (
        TransactionData,
        AgentStateData,
        MarketHistoryData,
        EconomicIndicatorData,
    )
    logging.basicConfig(level=logging.INFO)

    # 테스트 코드
    repo = SimulationRepository()

    # 테스트 런 생성
    run_id = repo.runs.save_simulation_run("test_hash", "Test Run")

    # 테스트 데이터 저장
    repo.markets.save_transaction(
        TransactionData(
            run_id=run_id,
            time=1,
            buyer_id=1,
            seller_id=2,
            item_id="food",
            quantity=10.0,
            price=5.0,
            market_id="goods_market",
            transaction_type="goods",
        )
    )
    repo.agents.save_agent_state(
        AgentStateData(
            run_id=run_id,
            time=1,
            agent_id=1,
            agent_type="household",
            assets=1000.0,
            is_active=True,
            is_employed=True,
            employer_id=10,
            needs_survival=50.0,
            needs_labor=20.0,
            inventory_food=5.0,
            current_production=None,
            num_employees=None,
        )
    )
    repo.analytics.save_economic_indicator(
        EconomicIndicatorData(
            run_id=run_id,
            time=1,
            unemployment_rate=5.0,
            avg_wage=1500.0,
            food_avg_price=5.0,
            total_production=100.0,
            total_consumption=50.0,
            total_household_assets=10000.0,
            total_firm_assets=5000.0,
            total_food_consumption=30.0,
            total_inventory=200.0,
        )
    )
    repo.markets.save_market_history(
        MarketHistoryData(
            time=1,
            market_id="goods_market",
            item_id="food",
            avg_price=5.0,
            trade_volume=100.0,
            best_ask=4.5,
            best_bid=5.5,
        )
    )

    # 테스트 데이터 조회
    logger.info(
        "\nEconomic Indicators (Tick 1): %s",
        repo.analytics.get_economic_indicators(start_tick=1, end_tick=1),
    )
    logger.info(
        "\nGoods Market History (Tick 1): %s",
        repo.markets.get_market_history(market_id="goods_market", start_tick=1, end_tick=1),
    )
    logger.info(
        "\nAgent 1 State (Tick 1): %s",
        repo.agents.get_agent_states(agent_id=1, start_tick=1, end_tick=1),
    )
    logger.info(
        "\nTransactions (Tick 1): %s", repo.markets.get_transactions(start_tick=1, end_tick=1)
    )

    repo.close()
    logger.info("\nRepository test completed.")
