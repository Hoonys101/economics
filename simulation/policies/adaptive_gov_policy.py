from typing import Dict, Any, TYPE_CHECKING
from simulation.interfaces.policy_interface import IGovernmentPolicy
from modules.government.policies.adaptive_gov_brain import AdaptiveGovBrain
from simulation.ai.enums import EconomicSchool
from simulation.dtos.policy_dtos import PolicyContextDTO, PolicyDecisionResultDTO, ActionRequestDTO
import logging

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

class AdaptiveGovPolicy(IGovernmentPolicy):
    """
    Policy implementation using AdaptiveGovBrain (Propose-Filter-Execute).
    Replaces legacy Q-Learning approach with Utility-Driven logic.
    """
    def __init__(self, government: Any, config_module: Any):
        self.config = config_module
        self.brain = AdaptiveGovBrain(config_module)
        # LockoutManager is in government agent

    def decide(self, context: PolicyContextDTO) -> PolicyDecisionResultDTO:
        current_tick = context.tick

        # 30-tick Interval (Optional, matching legacy behavior for stability)
        action_interval = getattr(self.config, "GOV_ACTION_INTERVAL", 30)
        if current_tick > 0 and current_tick % action_interval != 0:
            return PolicyDecisionResultDTO(policy_type="AI_UTILITY", status="COOLDOWN", action_taken="COOLDOWN")

        # 1. Propose
        # Ensure sensory_data is available
        sensory_data = context.sensory_data
        if not sensory_data:
             return PolicyDecisionResultDTO(policy_type="AI_UTILITY", status="NO_SENSORY_DATA", action_taken="No Sensory Data")

        proposed_actions = self.brain.propose_actions(sensory_data, context.ruling_party)

        # 2. Filter (Lockout)
        valid_actions = []
        for action in proposed_actions:
            if action.tag not in context.locked_policies:
                valid_actions.append(action)
            else:
                # Debug logging for lockout verification
                logger.debug(f"LOCKOUT_FILTER | Action {action.name} locked out.", extra={"tick": current_tick})

        if not valid_actions:
             return PolicyDecisionResultDTO(policy_type="AI_UTILITY", status="NO_VALID_ACTIONS", action_taken="No valid actions")

        # 3. Select (Max Utility)
        # They are already sorted by utility descending in brain
        best_action = valid_actions[0]

        # 4. Execute (Prepare Result)
        return self._prepare_execution_result(best_action, context)

    def _prepare_execution_result(self, action: Any, context: PolicyContextDTO) -> PolicyDecisionResultDTO:
         # Action Interpretation
         # action.action_type, action.params

         # TD-035: Generalized bounds from config
         welfare_min, welfare_max = 0.1, 2.0
         tax_min, tax_max = 0.05, 0.6

         # Try to resolve bounds from config
         try:
             # Check for object-style access (most likely based on codebase patterns)
             if hasattr(self.config, 'adaptive_policy'):
                 ap = self.config.adaptive_policy
                 if isinstance(ap, dict):
                     welfare_min, welfare_max = ap.get('welfare_bounds', [0.1, 2.0])
                     tax_min, tax_max = ap.get('tax_bounds', [0.05, 0.6])
                 else:
                     welfare_min, welfare_max = getattr(ap, 'welfare_bounds', [0.1, 2.0])
                     tax_min, tax_max = getattr(ap, 'tax_bounds', [0.05, 0.6])
             # Check for dict-style access
             elif isinstance(self.config, dict) and 'adaptive_policy' in self.config:
                 ap = self.config['adaptive_policy']
                 welfare_min, welfare_max = ap.get('welfare_bounds', [0.1, 2.0])
                 tax_min, tax_max = ap.get('tax_bounds', [0.05, 0.6])
         except Exception as e:
             logger.warning(f"Failed to load adaptive policy bounds from config: {e}. Using defaults.")

         result = PolicyDecisionResultDTO(
             policy_type="AI_UTILITY",
             action_taken=action.name,
             utility=action.utility,
             status="EXECUTED"
         )

         if action.action_type == "ADJUST_WELFARE":
             delta = action.params.get("multiplier_delta", 0.0)
             new_val = context.current_welfare_budget_multiplier + delta
             result.updated_welfare_budget_multiplier = max(welfare_min, min(welfare_max, new_val))

         elif action.action_type == "ADJUST_CORP_TAX":
             delta = action.params.get("rate_delta", 0.0)
             new_val = context.current_corporate_tax_rate + delta
             result.updated_corporate_tax_rate = max(tax_min, min(tax_max, new_val))

         elif action.action_type == "ADJUST_INCOME_TAX":
             delta = action.params.get("rate_delta", 0.0)
             new_val = context.current_income_tax_rate + delta
             result.updated_income_tax_rate = max(tax_min, min(tax_max, new_val))

         elif action.action_type == "FIRE_ADVISOR":
             # For now, default to firing the Keynesian advisor as they advocate for spending/intervention
             # Ideally, we should track which school's policies were active.
             result.action_request = ActionRequestDTO(
                 action_type="FIRE_ADVISOR",
                 target=EconomicSchool.KEYNESIAN
             )

         elif action.action_type == "DO_NOTHING":
             pass

         # Log
         if action.action_type != "DO_NOTHING":
             logger.info(f"POLICY_EXECUTE | {action.name} (U={action.utility:.4f})", extra={"tick": context.tick, "agent_id": context.agent_id})

         return result
