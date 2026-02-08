from typing import Dict, Any, TYPE_CHECKING
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.ai.enums import PoliticalParty
from simulation.dtos.policy_dtos import PolicyContextDTO, PolicyDecisionResultDTO
import logging

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

class SmartLeviathanPolicy(IGovernmentPolicy):
    """
    WO-057: Intelligent Policy Actuator (The Moving Hand).
    Translates Brain(Alpha) decisions into physical economic policy actions
    with safety bounds, baby steps, and party-specific implementation.
    """
    
    def __init__(self, government: Any, config_module: Any):
        self.config = config_module
        from simulation.ai.government_ai import GovernmentAI
        self.ai = GovernmentAI(government, config_module)
        self.last_action_tick = -999

    def decide(self, context: PolicyContextDTO) -> PolicyDecisionResultDTO:
        """
        Policy Decision Cycle.
        Enforces 30-tick (1 month) silent interval as per Architect Prime's Directive.
        """
        current_tick = context.tick
        action_interval = getattr(self.config, "GOV_ACTION_INTERVAL", 30)
        
        # 30-tick Interval Enforcement
        if current_tick > 0 and current_tick % action_interval != 0:
            return PolicyDecisionResultDTO(policy_type="AI_ADAPTIVE", status="COOLDOWN", action_taken="COOLDOWN")

        # 1. Observe and Decide (Brain)
        # Note: The AI's internal state representation is now directly tied to the
        # government agent's `sensory_data` attribute, which is updated by the engine.
        # FIXME: GovernmentAI still accesses government agent directly.
        action = self.ai.decide_policy(current_tick)
        self.last_action_tick = current_tick

        # --- [REFLEX OVERRIDE] ---
        # As per WO-067, a high inflation scenario must trigger an immediate hawkish response.
        # This overrides the learned Q-table behavior in critical situations to act as a safety backstop.
        current_state = self.ai._get_state()
        inflation_state = current_state[0]  # s_inf is the first element

        if inflation_state == 2:  # State 2 means "High Inflation"
            if action != self.ai.ACTION_HAWKISH:
                logger.warning(
                    f"REFLEX_OVERRIDE | High inflation detected (State={inflation_state}). "
                    f"Overriding AI action {action} with HAWKISH ({self.ai.ACTION_HAWKISH}).",
                    extra={"tick": current_tick}
                )
                action = self.ai.ACTION_HAWKISH
        # --- [END REFLEX OVERRIDE] ---

        # 2. Execution (Actuator)
        # Store old values for logging baby steps (using context)
        old_values = {
            "income_tax": context.current_income_tax_rate,
            "corp_tax": context.current_corporate_tax_rate,
            "welfare": context.current_welfare_budget_multiplier,
            "subsidy": 0.0 # subsidy multiplier is not in context yet, assuming default or need to add it?
            # context.current_welfare_budget_multiplier is available.
            # SmartLeviathanPolicy tracked firm_subsidy_budget_multiplier too.
        }
        # Assuming subsidy multiplier is same as welfare or separate.
        # context only has current_welfare_budget_multiplier.
        # I should add current_firm_subsidy_budget_multiplier to PolicyContextDTO if needed.
        # For now I will focus on welfare as it is in DTO.
        
        old_rate = context.central_bank_base_rate

        # Constants from Architect Directive
        steps = getattr(self.config, "POLICY_ACTUATOR_STEP_SIZES", (0.01, 0.0025, 0.1))
        TAX_STEP = steps[0]
        RATE_STEP = steps[1]
        BUDGET_STEP = steps[2]
        
        # New Values Initialization
        new_base_rate = old_rate
        new_corp_tax = context.current_corporate_tax_rate
        new_income_tax = context.current_income_tax_rate
        new_welfare_mult = context.current_welfare_budget_multiplier
        # new_subsidy_mult = context.current_firm_subsidy_budget_multiplier

        # 3. Translation Logic (Mapping Action -> Physical Change)
        if action == self.ai.ACTION_DOVISH:
            new_base_rate -= RATE_STEP
        
        elif action == self.ai.ACTION_HAWKISH:
             new_base_rate += RATE_STEP
        
        elif action == self.ai.ACTION_FISCAL_EASE:
            if context.ruling_party == PoliticalParty.BLUE:
                # Blue Expansion: Stimulate Firms
                new_corp_tax -= TAX_STEP
                # new_subsidy_mult += BUDGET_STEP
            else:
                # Red Expansion: Stimulate Households
                new_income_tax -= TAX_STEP
                new_welfare_mult += BUDGET_STEP
                
        elif action == self.ai.ACTION_FISCAL_TIGHT:
            if context.ruling_party == PoliticalParty.BLUE:
                # Blue Contraction: Shift burden to consumers
                new_income_tax += TAX_STEP
                new_welfare_mult -= BUDGET_STEP
            else:
                # Red Contraction: Shift burden to capital
                new_corp_tax += TAX_STEP
                # new_subsidy_mult -= BUDGET_STEP
        
        # 4. The Safety Valve (Clipping & Bounds)
        # Interest Rate [0% ~ 20%]
        new_base_rate = max(0.0, min(0.20, new_base_rate))
        
        # Tax Rate [5% ~ 50%]
        bounds = getattr(self.config, "POLICY_ACTUATOR_BOUNDS", {})
        tax_min, tax_max = bounds.get("tax", (0.05, 0.50))

        new_income_tax = max(tax_min, min(tax_max, new_income_tax))
        new_corp_tax = max(tax_min, min(tax_max, new_corp_tax))
        
        # Budget Allocation [10% ~ 100% or 200% in emergency]
        budget_min = getattr(self.config, "BUDGET_ALLOCATION_MIN", 0.1)

        # WO-057-Active: Emergency AI Levers
        budget_max = getattr(self.config, "NORMAL_BUDGET_MULTIPLIER_CAP", 1.0)
        if context.sensory_data:
            is_crisis = (context.sensory_data.gdp_growth_sma < -0.05 or
                         context.sensory_data.unemployment_sma > 0.10)
            if is_crisis:
                budget_max = getattr(self.config, "EMERGENCY_BUDGET_MULTIPLIER_CAP", 2.0)

        new_welfare_mult = max(budget_min, min(budget_max, new_welfare_mult))
        # new_subsidy_mult = max(budget_min, min(budget_max, new_subsidy_mult))

        # 5. Logging Baby Steps (Simplified)
        # self._log_changes(government, old_values, central_bank, old_rate, action, current_tick)
        # I'll rely on the caller or just log here if needed, but context doesn't have logger access easily (unless I import it).

        # 6. Reward & Learning
        self.ai.update_learning_with_state(reward=0.0, current_tick=current_tick)

        return PolicyDecisionResultDTO(
            policy_type="AI_ADAPTIVE",
            action_taken=str(action), # Ensure string
            status="EXECUTED" if action != self.ai.ACTION_NEUTRAL else "HOLD",
            updated_welfare_budget_multiplier=new_welfare_mult,
            updated_corporate_tax_rate=new_corp_tax,
            updated_income_tax_rate=new_income_tax,
            interest_rate_target=new_base_rate
        )
