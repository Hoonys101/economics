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
    시뮬레이션 데이터를 SQLite3 데이터베이스에 저장하고 조회하는 Repository 클래스입니다.
    Now acts as a facade for specialized repositories.
    """

    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

        # Initialize sub-repositories sharing the same connection
        self.agent_repo = AgentRepository(self.conn)
        self.market_repo = MarketRepository(self.conn)
        self.analytics_repo = AnalyticsRepository(self.conn)
        self.run_repo = RunRepository(self.conn)

    def save_simulation_run(self, config_hash: str, description: str) -> int:
        """
        새로운 시뮬레이션 실행 정보를 저장하고 실행 ID를 반환합니다.
        """
        return self.run_repo.save_simulation_run(config_hash, description)

    def update_simulation_run_end_time(self, run_id: int):
        """
        시뮬레이션 실행의 종료 시간을 업데이트합니다.
        """
        self.run_repo.update_simulation_run_end_time(run_id)

    def save_ai_decision(self, data: "AIDecisionData"):
        """
        AI 에이전트의 의사결정 데이터를 데이터베이스에 저장합니다.
        """
        self.analytics_repo.save_ai_decision(data)

    def clear_all_data(self):
        """
        모든 시뮬레이션 관련 테이블의 데이터를 삭제합니다.
        """
        try:
            self.market_repo.clear_data()
            self.agent_repo.clear_data()
            self.analytics_repo.clear_data()
            
            # Reclaim disk space
            self.cursor.execute("VACUUM")
            logger.info("All simulation data cleared and VACUUMed database.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing data: {e}")
            self.conn.rollback()

    def save_transaction(self, data: "TransactionData"):
        """
        단일 거래 데이터를 데이터베이스에 저장합니다.
        """
        self.market_repo.save_transaction(data)

    def save_agent_state(self, data: "AgentStateData"):
        """
        단일 에이전트 상태 데이터를 데이터베이스에 저장합니다.
        """
        self.agent_repo.save_agent_state(data)

    def save_market_history(self, data: "MarketHistoryData"):
        """
        단일 시장 이력 데이터를 데이터베이스에 저장합니다.
        """
        self.market_repo.save_market_history(data)

    def save_economic_indicator(self, data: "EconomicIndicatorData"):
        """
        단일 경제 지표 데이터를 데이터베이스에 저장합니다.
        """
        self.analytics_repo.save_economic_indicator(data)

    def save_agent_states_batch(self, agent_states_data: List["AgentStateData"]):
        """
        여러 에이전트 상태 데이터를 데이터베이스에 일괄 저장합니다.
        """
        self.agent_repo.save_agent_states_batch(agent_states_data)

    def save_transactions_batch(self, transactions_data: List["TransactionData"]):
        """
        여러 거래 데이터를 데이터베이스에 일괄 저장합니다.
        """
        self.market_repo.save_transactions_batch(transactions_data)

    def save_economic_indicators_batch(self, indicators_data: List["EconomicIndicatorData"]):
        """
        여러 경제 지표 데이터를 데이터베이스에 일괄 저장합니다.
        """
        self.analytics_repo.save_economic_indicators_batch(indicators_data)

    def save_market_history_batch(self, market_history_data: List["MarketHistoryData"]):
        """
        여러 시장 이력 데이터를 데이터베이스에 일괄 저장합니다.
        """
        self.market_repo.save_market_history_batch(market_history_data)

    def get_economic_indicators(
        self, start_tick: Optional[int] = None, end_tick: Optional[int] = None, run_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        경제 지표 데이터를 조회합니다.
        """
        return self.analytics_repo.get_economic_indicators(start_tick, end_tick, run_id)

    def get_latest_economic_indicator(self, indicator_name: str) -> Optional[float]:
        """
        특정 경제 지표의 최신 값을 조회합니다.
        """
        return self.analytics_repo.get_latest_economic_indicator(indicator_name)

    def get_market_history(
        self,
        market_id: str,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        item_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 시장의 이력 데이터를 조회합니다.
        """
        return self.market_repo.get_market_history(market_id, start_tick, end_tick, item_id)

    def get_agent_states(
        self,
        agent_id: int,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 에이전트의 상태 변화 이력을 조회합니다.
        """
        return self.agent_repo.get_agent_states(agent_id, start_tick, end_tick)

    def get_transactions(
        self,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        market_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        거래 데이터를 조회합니다.
        """
        return self.market_repo.get_transactions(start_tick, end_tick, market_id)

    def close(self):
        """
        Repository 사용을 마칠 때 데이터베이스 연결을 닫습니다.
        """
        close_db_connection()

    def get_generation_stats(self, tick: int, run_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        특정 틱의 세대별 인구 및 자산 통계를 조회합니다.
        """
        return self.agent_repo.get_generation_stats(tick, run_id)

    def get_attrition_counts(self, start_tick: int, end_tick: int, run_id: Optional[int] = None) -> Dict[str, int]:
        """
        Calculates the number of agents that became inactive (bankruptcy/death) between start_tick and end_tick.
        """
        return self.agent_repo.get_attrition_counts(start_tick, end_tick, run_id)


if __name__ == "__main__":
    # 테스트 코드
    repo = SimulationRepository()

    # 테스트 런 생성
    run_id = repo.save_simulation_run("test_hash", "Test Run")

    # 테스트 데이터 저장
    repo.save_transaction(
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
    repo.save_agent_state(
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
    repo.save_economic_indicator(
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
    repo.save_market_history(
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
        repo.get_economic_indicators(start_tick=1, end_tick=1),
    )
    logger.info(
        "\nGoods Market History (Tick 1): %s",
        repo.get_market_history(market_id="goods_market", start_tick=1, end_tick=1),
    )
    logger.info(
        "\nAgent 1 State (Tick 1): %s",
        repo.get_agent_states(agent_id=1, start_tick=1, end_tick=1),
    )
    logger.info(
        "\nTransactions (Tick 1): %s", repo.get_transactions(start_tick=1, end_tick=1)
    )

    repo.close()
    logger.info("\nRepository test completed.")
