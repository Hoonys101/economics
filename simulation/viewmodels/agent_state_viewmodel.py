from typing import List, Dict, Any, Optional
from simulation.db.repository import SimulationRepository
import logging


class AgentStateViewModel:
    """
    개별 에이전트의 상태 변화 데이터를 웹 UI에 제공하기 위한 ViewModel입니다.
    SimulationRepository를 통해 데이터를 조회하고, 필요한 형태로 가공합니다.
    """

    def __init__(self, repository: Optional[SimulationRepository] = None):
        self.repository = repository if repository else SimulationRepository()

    def get_agent_states(
        self,
        agent_id: int,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        특정 에이전트의 상태 변화 데이터를 조회하여 반환합니다.
        """
        states = self.repository.get_agent_states(agent_id, start_tick, end_tick)
        return states

    def get_agent_assets_data(
        self,
        agent_id: int,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
    ) -> Dict[str, List[Any]]:
        """
        특정 에이전트의 자산 변화 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        """
        states = self.get_agent_states(agent_id, start_tick, end_tick)
        times = [s["time"] for s in states]
        assets = [s["assets"] for s in states]

        return {
            "labels": times,
            "datasets": [
                {
                    "label": f"에이전트 {agent_id} 자산",
                    "data": assets,
                    "borderColor": "rgb(0, 123, 255)",
                    "tension": 0.1,
                }
            ],
        }

    def get_agent_employment_data(
        self,
        agent_id: int,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
    ) -> Dict[str, List[Any]]:
        """
        특정 가계 에이전트의 고용 상태 변화 차트 데이터를 Chart.js 형식에 맞게 가공하여 반환합니다.
        (0: 실업, 1: 고용)
        """
        states = self.get_agent_states(agent_id, start_tick, end_tick)
        times = [s["time"] for s in states]
        # is_employed는 BOOLEAN으로 저장되므로 0 또는 1로 변환
        employment_status = [
            1 if s["is_employed"] else 0
            for s in states
            if s["agent_type"] == "household"
        ]

        return {
            "labels": times,
            "datasets": [
                {
                    "label": f"가계 {agent_id} 고용 상태",
                    "data": employment_status,
                    "borderColor": "rgb(40, 167, 69)",
                    "stepSize": 1,  # 고용 상태는 0 또는 1이므로 계단식으로 표시
                    "tension": 0.1,
                }
            ],
        }


if __name__ == "__main__":
    # 테스트 코드
    # 이 테스트를 실행하기 전에 simulation_data.db 파일이 존재하고 데이터가 채워져 있어야 합니다.
    # main.py를 한 번 실행하여 데이터를 생성한 후 이 테스트를 실행하세요.

    repo = SimulationRepository()
    vm = AgentStateViewModel(repo)

    # 예시: 에이전트 1의 상태 이력 조회
    logging.info(f"Agent 1 States (all): {vm.get_agent_states(agent_id=1)}")
    logging.info(
        f"Agent 1 Assets Data (Chart.js format): {vm.get_agent_assets_data(agent_id=1)}"
    )
    logging.info(
        f"Agent 1 Employment Data (Chart.js format): {vm.get_agent_employment_data(agent_id=1)}"
    )

    repo.close()
