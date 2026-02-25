from _typeshed import Incomplete
from simulation.ai.model_wrapper import ModelWrapper as ModelWrapper
from simulation.ai.state_builder import StateBuilder as StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine as ActionProposalEngine
from typing import Any

logger: Incomplete

class AIDecisionEngine:
    """
    AI 에이전트의 의사결정을 총괄하는 엔진.
    ModelWrapper를 사용하여 예측하고, BaseAIEngine의 추상 메서드를 구현하여
    실제 에이전트의 상태, 행동, 보상 로직을 연결한다.
    """
    value_orientation: Incomplete
    model_wrapper: Incomplete
    action_proposal_engine: Incomplete
    state_builder: Incomplete
    is_trained: Incomplete
    def __init__(self, value_orientation: str, action_proposal_engine: ActionProposalEngine, state_builder: StateBuilder) -> None: ...
    def get_predicted_reward(self, agent_data: dict[str, Any], market_data: dict[str, Any]) -> float:
        """
        에이전트의 현재 상태를 기반으로 ModelWrapper를 사용하여 예상 보상을 예측한다.
        """
    def train(self, states: list[dict[str, Any]], rewards: list[float]):
        """
        ModelWrapper를 사용하여 모델을 훈련시킨다.
        """
    def save_model(self) -> None:
        """
        ModelWrapper를 통해 모델을 저장한다.
        """
    def load_model(self) -> None:
        """
        ModelWrapper를 통해 모델을 로드한다.
        """

class AIEngineRegistry:
    """AI 의사결정 엔진을 생성하고 관리하는 레지스트리 클래스입니다."""
    def __init__(self, action_proposal_engine: ActionProposalEngine, state_builder: StateBuilder) -> None: ...
    def get_engine(self, value_orientation: str) -> AIDecisionEngine:
        """
        주어진 가치관에 대한 AI 의사결정 엔진을 반환합니다. 없으면 새로 생성합니다.
        """
    def end_episode(self, all_agents: list[Any]):
        """
        에피소드(시뮬레이션) 종료 시 모든 AI 모델을 저장한다.
        """
    def inherit_brain(self, parent: Any, child: Any) -> None:
        """
        Copies decision making policies/weights from parent to child.
        Legacy support for 'demographic_manager.process_births'.
        For now, this is a no-op as the shared model is used via get_engine.
        If individual learning is implemented, this would copy specific weights.
        """
