from _typeshed import Incomplete
from simulation.db.base_repository import BaseRepository as BaseRepository

logger: Incomplete

class RunRepository(BaseRepository):
    """
    Repository for managing simulation runs.
    """
    def save_simulation_run(self, config_hash: str, description: str) -> int:
        """
        새로운 시뮬레이션 실행 정보를 저장하고 실행 ID를 반환합니다.
        """
    def update_simulation_run_end_time(self, run_id: int):
        """
        시뮬레이션 실행의 종료 시간을 업데이트합니다.
        """
