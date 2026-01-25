import logging
from typing import Dict, Any, List, TYPE_CHECKING
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class SystemEffectsManager:
    """
    Manages deferred side-effects from transactions.
    Enforces the 'Sacred Sequence' by decoupling decision/action from state modification consequences.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

    def process_effects(self, state: SimulationState) -> None:
        """
        Processes all effects in the state.effects_queue.
        """
        if not state.effects_queue:
            return

        for effect in state.effects_queue:
            effect_type = effect.get("triggers_effect")
            if effect_type == "GLOBAL_TFP_BOOST":
                self._apply_global_tfp_boost(state)
            else:
                logger.warning(f"UNKNOWN_EFFECT | Encountered unknown effect type: {effect_type}")

        # Clear queue after processing
        state.effects_queue.clear()

    def _apply_global_tfp_boost(self, state: SimulationState) -> None:
        """
        Applies a productivity boost to all active firms.
        """
        tfp_boost = getattr(self.config_module, "INFRASTRUCTURE_TFP_BOOST", 0.05)
        count = 0
        for firm in state.firms:
            if firm.is_active:
                firm.productivity_factor *= (1.0 + tfp_boost)
                count += 1

        logger.info(
            f"GLOBAL_TFP_BOOST | Applied {tfp_boost*100:.1f}% productivity increase to {count} firms.",
            extra={"tick": state.time, "tags": ["system_effect", "infrastructure"]}
        )
