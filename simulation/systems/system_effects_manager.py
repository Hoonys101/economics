import logging
import random
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
            elif effect_type == "GOVERNMENT_INFRA_UPGRADE":
                self._apply_gov_infra_upgrade(state)
            elif effect_type == "EDUCATION_UPGRADE":
                self._apply_education_upgrade(state, effect)
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

    def _apply_gov_infra_upgrade(self, state: SimulationState) -> None:
        """Increments the government infrastructure level."""
        if state.primary_government:
            state.primary_government.infrastructure_level += 1
            # Link to productivity increase
            self._apply_global_tfp_boost(state)
            logger.info(
                f"GOVERNMENT_INFRA_UPGRADE | Level increased to {state.primary_government.infrastructure_level}.",
                extra={"tick": state.time, "tags": ["system_effect", "infrastructure"]}
            )

    def _apply_education_upgrade(self, state: SimulationState, effect: Dict[str, Any]) -> None:
        """Increments education level for a specific household."""
        target_id = effect.get("target_agent_id")
        if target_id is None:
            return

        household = state.agents.get(target_id)
        if household:
            old_level = household._econ_state.education_level
            new_level = old_level + 1
            household._econ_state.education_level = new_level

            # Phase 4.1: Blind Major Choice Logic
            # Triggered when entering Higher Education (Level 1+)
            # Only assign if currently GENERAL or None, to support Sunk Cost (no switching)
            current_major = getattr(household._econ_state, "major", "GENERAL")
            if new_level >= 1 and (current_major == "GENERAL" or current_major is None):
                # Retrieve available majors from config or default
                labor_config = getattr(self.config_module, "LABOR_MARKET", {})
                # Handle both dict (if loaded as dict) and object (if loaded as config module)
                if isinstance(labor_config, dict):
                     available_majors = labor_config.get("majors", ["GENERAL"])
                else:
                     available_majors = getattr(labor_config, "majors", ["GENERAL"])

                # Exclude GENERAL from specialized choice if possible
                specialized_majors = [m for m in available_majors if m != "GENERAL"]

                if specialized_majors:
                    # Blind Choice: Random selection
                    chosen_major = random.choice(specialized_majors)
                    household._econ_state.major = chosen_major

                    logger.info(
                        f"MAJOR_CHOICE | Household {target_id} selected major: {chosen_major}",
                        extra={"tick": state.time, "tags": ["education", "major_choice"]}
                    )

            logger.info(
                f"EDUCATION_UPGRADE | Household {target_id} promoted to Level {household._econ_state.education_level}.",
                extra={"tick": state.time, "tags": ["system_effect", "education"]}
            )
