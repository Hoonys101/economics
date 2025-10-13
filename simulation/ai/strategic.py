"""
Level 1 AI: StrategicAI

Decides the high-level Intention for an agent.
"""

from typing import Dict, Any
import logging

from simulation.ai.api import BaseDecisionAI, Intention
from simulation.core_agents import BaseAgent

logger = logging.getLogger(__name__)


class StrategicAI(BaseDecisionAI):
    """
    The Level 1 AI responsible for determining the agent's high-level strategic goal (Intention)
    for the current tick.
    """

    def __init__(self):
        # In the future, this will load a trained model for strategic decision-making.
        self.model = None  # Placeholder for the actual ML model
        logger.info(
            "StrategicAI initialized.", extra={"tags": ["init", "ai", "strategic"]}
        )

    def make_decision(self, agent: BaseAgent, market_data: Dict[str, Any]) -> Intention:
        """
        Makes a strategic decision by selecting a high-level Intention.

        Args:
            agent: The agent making the decision.
            market_data: Current data from all relevant markets.

        Returns:
            An Intention Enum member representing the chosen strategic goal.
        """
        log_extra = {
            "tick": market_data.get("current_tick", 0),
            "agent_id": agent.id,
            "tags": ["ai_decision", "strategic"],
        }

        # TODO: Implement actual state building and model prediction
        # For now, this is a placeholder implementation.
        if self.model is None:
            logger.warning(
                "StrategicAI model not loaded. Returning default Intention: DO_NOTHING.",
                extra=log_extra,
            )
            # Placeholder logic: if survival need is high, focus on that.
            if agent.needs.get("survival_need", 0) > 50:
                return Intention.SATISFY_SURVIVAL_NEED
            return Intention.DO_NOTHING

        # state = self._build_state(agent, market_data)
        # predicted_intention = self.model.predict(state)
        # return predicted_intention
        return Intention.DO_NOTHING