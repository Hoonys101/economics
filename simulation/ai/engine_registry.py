from __future__ import annotations
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine
    from simulation.decisions.action_proposal import ActionProposalEngine
    from simulation.ai.state_builder import StateBuilder

class AIEngineRegistry:
    """AI 의사결정 엔진을 생성하고 관리하는 레지스트리 클래스입니다."""

    def __init__(self, action_proposal_engine: ActionProposalEngine, state_builder: StateBuilder):
        self._engines: Dict[str, AIDecisionEngine] = {}
        self._action_proposal_engine = action_proposal_engine
        self._state_builder = state_builder

    def get_engine(self, value_orientation: str) -> AIDecisionEngine:
        """주어진 가치관에 대한 AI 의사결정 엔진을 반환합니다. 없으면 새로 생성합니다."""
        if value_orientation not in self._engines:
            from simulation.ai_model import AIDecisionEngine
            engine = AIDecisionEngine(
                value_orientation=value_orientation,
                action_proposal_engine=self._action_proposal_engine,
                state_builder=self._state_builder
            )
            self._engines[value_orientation] = engine
        return self._engines[value_orientation]
