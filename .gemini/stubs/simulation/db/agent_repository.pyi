from _typeshed import Incomplete
from simulation.db.base_repository import BaseRepository as BaseRepository
from simulation.dtos import AgentStateData as AgentStateData
from typing import Any

logger: Incomplete

class AgentRepository(BaseRepository):
    """
    Repository for managing agent state data.
    """
    def save_agent_state(self, data: AgentStateData):
        """
        단일 에이전트 상태 데이터를 데이터베이스에 저장합니다.
        """
    def save_agent_states_batch(self, agent_states_data: list['AgentStateData']):
        """
        여러 에이전트 상태 데이터를 데이터베이스에 일괄 저장합니다.
        """
    def get_agent_states(self, agent_id: int, start_tick: int | None = None, end_tick: int | None = None) -> list[dict[str, Any]]:
        """
        특정 에이전트의 상태 변화 이력을 조회합니다.
        """
    def get_generation_stats(self, tick: int, run_id: int | None = None) -> list[dict[str, Any]]:
        """
        특정 틱의 세대별 인구 및 자산 통계를 조회합니다.
        """
    def get_attrition_counts(self, start_tick: int, end_tick: int, run_id: int | None = None) -> dict[str, int]:
        '''
        Calculates the number of agents that became inactive (bankruptcy/death) between start_tick and end_tick.

        Args:
            start_tick: The starting tick of the window (inclusive).
            end_tick: The ending tick of the window (inclusive).
            run_id: The simulation run ID.

        Returns:
            Dict with keys "bankruptcy_count" and "death_count".
        '''
    def get_birth_counts(self, start_tick: int, end_tick: int, run_id: int | None = None) -> int:
        """
        Calculates the number of NEW households that appeared between start_tick and end_tick.
        Specifically, counts agents present at end_tick who were NOT present at start_tick.
        """
    def clear_data(self) -> None:
        """
        agent_states 테이블의 데이터를 삭제합니다.
        """
