from typing import Dict, Any, TYPE_CHECKING
from simulation.interfaces.policy_interface import IGovernmentPolicy
from modules.government.policies.adaptive_gov_brain import AdaptiveGovBrain
from simulation.ai.enums import EconomicSchool
import logging

if TYPE_CHECKING:
    from simulation.agents.government import Government
    from simulation.dtos import GovernmentSensoryDTO
    from simulation.agents.central_bank import CentralBank

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

    def decide(self, government: "Government", sensory_data: "GovernmentSensoryDTO", current_tick: int, central_bank: "CentralBank") -> Dict[str, Any]:

        # 30-tick Interval (Optional, matching legacy behavior for stability)
        action_interval = getattr(self.config, "GOV_ACTION_INTERVAL", 30)
        if current_tick > 0 and current_tick % action_interval != 0:
            return {"policy_type": "AI_UTILITY", "status": "COOLDOWN"}

        # 1. Propose
        # Ensure sensory_data is available
        if not sensory_data:
             return {"policy_type": "AI_UTILITY", "status": "NO_SENSORY_DATA"}

        proposed_actions = self.brain.propose_actions(sensory_data, government.ruling_party)

        # 2. Filter (Lockout)
        valid_actions = []
        for action in proposed_actions:
            if not government.policy_lockout_manager.is_locked(action.tag, current_tick):
                valid_actions.append(action)
            else:
                # Debug logging for lockout verification
                logger.debug(f"LOCKOUT_FILTER | Action {action.name} locked out.", extra={"tick": current_tick})

        if not valid_actions:
             return {"policy_type": "AI_UTILITY", "status": "NO_VALID_ACTIONS"}

        # 3. Select (Max Utility)
        # They are already sorted by utility descending in brain
        best_action = valid_actions[0]

        # 4. Execute
        self._execute_action(government, best_action, current_tick)

        return {
            "policy_type": "AI_UTILITY",
            "action_taken": best_action.name,
            "utility": best_action.utility,
            "status": "EXECUTED"
        }

    def _execute_action(self, government: "Government", action: Any, tick: int):
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

         if action.action_type == "ADJUST_WELFARE":
             delta = action.params.get("multiplier_delta", 0.0)
             government.welfare_budget_multiplier += delta
             # Clamp
             government.welfare_budget_multiplier = max(welfare_min, min(welfare_max, government.welfare_budget_multiplier))

         elif action.action_type == "ADJUST_CORP_TAX":
             delta = action.params.get("rate_delta", 0.0)
             government.corporate_tax_rate += delta
             government.corporate_tax_rate = max(tax_min, min(tax_max, government.corporate_tax_rate))

         elif action.action_type == "ADJUST_INCOME_TAX":
             delta = action.params.get("rate_delta", 0.0)
             government.income_tax_rate += delta
             government.income_tax_rate = max(tax_min, min(tax_max, government.income_tax_rate))

         elif action.action_type == "FIRE_ADVISOR":
             # For now, default to firing the Keynesian advisor as they advocate for spending/intervention
             # Ideally, we should track which school's policies were active.
             government.fire_advisor(EconomicSchool.KEYNESIAN, tick)

         elif action.action_type == "DO_NOTHING":
             pass

         # Log
         if action.action_type != "DO_NOTHING":
             logger.info(f"POLICY_EXECUTE | {action.name} (U={action.utility:.4f})", extra={"tick": tick, "agent_id": government.id})
