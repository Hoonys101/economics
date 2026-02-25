from _typeshed import Incomplete
from datetime import datetime as datetime
from simulation.db.agent_repository import AgentRepository as AgentRepository
from simulation.db.analytics_repository import AnalyticsRepository as AnalyticsRepository
from simulation.db.database import close_db_connection as close_db_connection, get_db_connection as get_db_connection
from simulation.db.market_repository import MarketRepository as MarketRepository
from simulation.db.migration import SchemaMigrator as SchemaMigrator
from simulation.db.run_repository import RunRepository as RunRepository
from simulation.dtos import AIDecisionData as AIDecisionData, AgentStateData as AgentStateData, EconomicIndicatorData as EconomicIndicatorData, MarketHistoryData as MarketHistoryData, TransactionData as TransactionData

logger: Incomplete

class SimulationRepository:
    """
    Unit of Work container for simulation repositories.
    Provides access to domain-specific repositories sharing the same database connection.
    """
    conn: Incomplete
    agents: Incomplete
    markets: Incomplete
    analytics: Incomplete
    runs: Incomplete
    def __init__(self) -> None: ...
    def migrate(self) -> None:
        """
        Executes database schema migration.
        """
    def clear_all_data(self) -> None:
        """
        모든 시뮬레이션 관련 테이블의 데이터를 삭제합니다.
        """
    def close(self) -> None:
        """
        Repository 사용을 마칠 때 데이터베이스 연결을 닫습니다.
        """
