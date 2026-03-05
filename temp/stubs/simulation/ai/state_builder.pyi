from typing import Any

class StateBuilder:
    def build_state(self, agent_data: dict[str, Any], market_data: dict[str, Any], value_orientation: str) -> dict[str, Any]:
        """
        에이전트의 현재 상태와 시장 데이터를 기반으로 AI 모델이 사용할 상태를 dict 형태로 반환합니다.
        """
