# simulation/ai_model.py

import logging
from typing import Any, Dict, List, TYPE_CHECKING

from simulation.ai.model_wrapper import ModelWrapper
# from simulation.ai.engine_registry import AIEngineRegistry # Removed to avoid circular import

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simulation.decisions.action_proposal import ActionProposalEngine
    from simulation.ai.state_builder import StateBuilder


class AIDecisionEngine:
    """
    AI 에이전트의 의사결정을 총괄하는 엔진.
    ModelWrapper를 사용하여 예측하고, BaseAIEngine의 추상 메서드를 구현하여
    실제 에이전트의 상태, 행동, 보상 로직을 연결한다.
    """

    def __init__(
        self,
        value_orientation: str,
        action_proposal_engine: "ActionProposalEngine",
        state_builder: "StateBuilder",
    ):
        self.value_orientation = value_orientation
        self.model_wrapper = ModelWrapper(value_orientation)
        self.model_wrapper.load()  # Load existing model if available
        self.action_proposal_engine = action_proposal_engine
        self.state_builder = state_builder
        self.is_trained = (
            self.model_wrapper.is_trained
        )  # Track if the underlying model is trained

    def get_predicted_reward(
        self, agent_data: Dict[str, Any], market_data: Dict[str, Any]
    ) -> float:
        """
        에이전트의 현재 상태를 기반으로 ModelWrapper를 사용하여 예상 보상을 예측한다.
        """
        current_state_dict = self.state_builder.build_state(
            agent_data, market_data, self.value_orientation
        )
        predicted_reward = self.model_wrapper.predict(current_state_dict)

        logger.debug(
            f"AIDecisionEngine | Predicted reward: {predicted_reward}",
            extra={"tags": ["ai_prediction_debug"]},
        )
        return predicted_reward

    def train(self, states: List[Dict[str, Any]], rewards: List[float]):
        """
        ModelWrapper를 사용하여 모델을 훈련시킨다.
        """
        self.model_wrapper.train(states, rewards)
        self.is_trained = self.model_wrapper.is_trained

    def save_model(self):
        """
        ModelWrapper를 통해 모델을 저장한다.
        """
        self.model_wrapper.save()

    def load_model(self):
        """
        ModelWrapper를 통해 모델을 로드한다.
        """
        self.model_wrapper.load()
        self.is_trained = self.model_wrapper.is_trained


class AIEngineRegistry:
    """AI 의사결정 엔진을 생성하고 관리하는 레지스트리 클래스입니다."""

    def __init__(
        self,
        action_proposal_engine: "ActionProposalEngine",
        state_builder: "StateBuilder",
    ):
        self._engines: Dict[str, AIDecisionEngine] = {}
        self._action_proposal_engine = action_proposal_engine
        self._state_builder = state_builder

    def get_engine(self, value_orientation: str) -> AIDecisionEngine:
        """
        주어진 가치관에 대한 AI 의사결정 엔진을 반환합니다. 없으면 새로 생성합니다.
        """
        if value_orientation not in self._engines:
            # AIDecisionEngine은 action_proposal_engine과 state_builder를 필요로 함.
            engine = AIDecisionEngine(
                value_orientation=value_orientation,
                action_proposal_engine=self._action_proposal_engine,
                state_builder=self._state_builder,
            )
            self._engines[value_orientation] = engine
        return self._engines[value_orientation]

    def end_episode(self, all_agents: List[Any]):
        """
        에피소드(시뮬레이션) 종료 시 모든 AI 모델을 저장한다.
        """
        for engine in self._engines.values():
            engine.save_model()
        logger.info(
            "All AI models saved at the end of the episode.",
            extra={"tags": ["ai_model", "save_all"]},
        )

    def inherit_brain(self, parent: Any, child: Any) -> None:
        """
        Copies decision making policies/weights from parent to child.
        Legacy support for 'demographic_manager.process_births'.
        For now, this is a no-op as the shared model is used via get_engine.
        If individual learning is implemented, this would copy specific weights.
        """
        # In current architecture, agents share the same model instance based on Value Orientation.
        # So explicit weight copying is not needed unless we have per-agent models.
        # But we must implement this method to prevent AttributeError.
        pass
