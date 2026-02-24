from typing import Dict, Any, Optional
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.ai.enums import PoliticalParty
from modules.government.ai.api import AIConfigDTO
from modules.government.dtos import GovernmentStateDTO, GovernmentPolicyDTO, GovernmentSensoryDTO
import logging

logger = logging.getLogger(__name__)

class SmartLeviathanPolicy(IGovernmentPolicy):
    """
    WO-057: Intelligent Policy Actuator (The Moving Hand).
    Translates Brain(Alpha) decisions into physical economic policy actions
    with safety bounds, baby steps, and party-specific implementation.
    """
    
    def __init__(self, government: Any, config_module: Any):
        self.config = config_module

        # Initialize AI Config
        ai_config = AIConfigDTO(
            alpha=getattr(config_module, "RL_LEARNING_RATE", 0.1),
            gamma=getattr(config_module, "RL_DISCOUNT_FACTOR", 0.95),
            epsilon=getattr(config_module, "AI_EPSILON", 0.1),
            enable_reflex_override=getattr(config_module, "ENABLE_REFLEX_OVERRIDE", False),
            w_approval=getattr(config_module, "AI_W_APPROVAL", 0.7),
            w_stability=getattr(config_module, "AI_W_STABILITY", 0.2),
            w_lobbying=getattr(config_module, "AI_W_LOBBYING", 0.1)
        )

        from simulation.ai.government_ai import GovernmentAI
        self.ai = GovernmentAI(government, ai_config)
        self.last_action_tick = -999

    def decide(self, government: Any, sensory_data: "GovernmentSensoryDTO", current_tick: int, central_bank: Any = None) -> Dict[str, Any]:
        """
        Policy Decision Cycle.
        Enforces 30-tick (1 month) silent interval as per Architect Prime's Directive.
        """
        action_interval = getattr(self.config, "GOV_ACTION_INTERVAL", 30)
        
        # 30-tick Interval Enforcement
        if current_tick > 0 and current_tick % action_interval != 0:
            return {"policy_type": "AI_ADAPTIVE", "status": "COOLDOWN"}

        # Construct GovernmentStateDTO for the AI

        # Determine Total Debt with Fallback
        total_debt = getattr(government, 'total_debt', None)
        if total_debt is None:
            # Fallback for mock agents or legacy models without total_debt attribute
            # Calculate from total_wealth (if negative)
            total_wealth = getattr(government, 'total_wealth', getattr(government, 'assets', 0))
            if isinstance(total_wealth, dict):
                 total_wealth = sum(total_wealth.values())
            total_debt = max(0, -total_wealth)

        policy_dto = getattr(government, 'policy', None)
        # Fallback if policy is missing (e.g. mock)
        if not policy_dto:
             policy_dto = GovernmentPolicyDTO()

        state_dto = GovernmentStateDTO(
            tick=current_tick,
            assets=getattr(government, 'assets', {}),
            total_debt=total_debt,
            income_tax_rate=getattr(government, 'income_tax_rate', 0.2),
            corporate_tax_rate=getattr(government, 'corporate_tax_rate', 0.2),
            policy=policy_dto,
            approval_rating=getattr(government, 'approval_rating', 0.5),
            sensory_data=getattr(government, 'sensory_data', None),
            ruling_party=getattr(government, 'ruling_party', None),
            welfare_budget_multiplier=getattr(government, 'welfare_budget_multiplier', 1.0),
            # Optional fields with safe defaults
            fiscal_policy=getattr(government, 'fiscal_policy', None),
            policy_lockouts=getattr(government, 'policy_lockouts', {}),
            gdp_history=getattr(government, 'gdp_history', []),
            potential_gdp=getattr(government, 'potential_gdp', 0.0),
            fiscal_stance=getattr(government, 'fiscal_stance', 0.0)
        )

        # 1. Learn from the PAST (Reward for action at T-interval)
        # This must happen BEFORE deciding the new action overwrites self.last_state
        self.ai.update_learning(current_tick, state_dto)

        # 2. Observe and Decide (Brain)
        # This sets self.last_state = current_state
        action = self.ai.decide_policy(current_tick, state_dto)
        self.last_action_tick = current_tick

        # --- [REFLEX OVERRIDE] ---
        # As per Wave 5, this is now Configurable.
        # We check the AI's internal state (last_state) for Inflation (Index 0).
        if self.ai.config.enable_reflex_override:
            # Check if last state was High Inflation (2)
            if self.ai.last_state and self.ai.last_state[0] == 2:
                if action != self.ai.ACTION_HAWKISH:
                    logger.warning(
                        f"REFLEX_OVERRIDE | High inflation detected. "
                        f"Overriding AI action {action} with HAWKISH ({self.ai.ACTION_HAWKISH}).",
                        extra={"tick": current_tick}
                    )
                    action = self.ai.ACTION_HAWKISH
        # --- [END REFLEX OVERRIDE] ---

        # 3. Execution (Actuator)
        # Store old values for logging baby steps
        old_values = {
            "income_tax": government.income_tax_rate,
            "corp_tax": government.corporate_tax_rate,
            "welfare": government.welfare_budget_multiplier,
            "subsidy": government.firm_subsidy_budget_multiplier
        }
        
        old_rate = central_bank.base_rate if central_bank else 0.0

        # Constants from Architect Directive
        steps = getattr(self.config, "POLICY_ACTUATOR_STEP_SIZES", (0.01, 0.0025, 0.1))
        TAX_STEP = steps[0]
        RATE_STEP = steps[1]
        BUDGET_STEP = steps[2]
        
        # 4. Translation Logic (Mapping Action -> Physical Change)
        if action == self.ai.ACTION_DOVISH:
            if central_bank:
                central_bank.base_rate -= RATE_STEP
        
        elif action == self.ai.ACTION_HAWKISH:
            if central_bank:
                central_bank.base_rate += RATE_STEP
        
        elif action == self.ai.ACTION_FISCAL_EASE:
            if government.ruling_party == PoliticalParty.BLUE:
                # Blue Expansion: Stimulate Firms
                government.corporate_tax_rate -= TAX_STEP
                government.firm_subsidy_budget_multiplier += BUDGET_STEP
            else:
                # Red Expansion: Stimulate Households
                government.income_tax_rate -= TAX_STEP
                government.welfare_budget_multiplier += BUDGET_STEP
                
        elif action == self.ai.ACTION_FISCAL_TIGHT:
            if government.ruling_party == PoliticalParty.BLUE:
                # Blue Contraction: Shift burden to consumers
                government.income_tax_rate += TAX_STEP
                government.welfare_budget_multiplier -= BUDGET_STEP
            else:
                # Red Contraction: Shift burden to capital
                government.corporate_tax_rate += TAX_STEP
                government.firm_subsidy_budget_multiplier -= BUDGET_STEP
        
        # 5. The Safety Valve (Clipping & Bounds)
        # Interest Rate [0% ~ 20%]
        if central_bank:
            central_bank.base_rate = max(0.0, min(0.20, central_bank.base_rate))
        
        # Tax Rate [5% ~ 50%]
        bounds = getattr(self.config, "POLICY_ACTUATOR_BOUNDS", {})
        tax_min, tax_max = bounds.get("tax", (0.05, 0.50))

        government.income_tax_rate = max(tax_min, min(tax_max, government.income_tax_rate))
        government.corporate_tax_rate = max(tax_min, min(tax_max, government.corporate_tax_rate))
        
        # Budget Allocation [10% ~ 100% or 200% in emergency]
        budget_min = getattr(self.config, "BUDGET_ALLOCATION_MIN", 0.1)

        # WO-057-Active: Emergency AI Levers
        budget_max = getattr(self.config, "NORMAL_BUDGET_MULTIPLIER_CAP", 1.0)
        if government.sensory_data:
            is_crisis = (government.sensory_data.gdp_growth_sma < -0.05 or
                         government.sensory_data.unemployment_sma > 0.10)
            if is_crisis:
                budget_max = getattr(self.config, "EMERGENCY_BUDGET_MULTIPLIER_CAP", 2.0)

        government.welfare_budget_multiplier = max(budget_min, min(budget_max, government.welfare_budget_multiplier))
        government.firm_subsidy_budget_multiplier = max(budget_min, min(budget_max, government.firm_subsidy_budget_multiplier))

        # 6. Logging Baby Steps
        self._log_changes(government, old_values, central_bank, old_rate, action, current_tick)

        # Note: Learning step moved to top of loop to prevent self-loop bug.

        return {
            "policy_type": "AI_ADAPTIVE",
            "action_taken": action,
            "status": "EXECUTED" if action != self.ai.ACTION_NEUTRAL else "HOLD"
        }

    def _log_changes(self, gov, old_val, cb, old_rate, action, tick):
        if action == 1: # Neutral
            return

        log_tag = {"extra": {"tick": tick, "agent_id": gov.id, "tags": ["policy", "babystep"]}}
        
        if cb and abs(old_rate - cb.base_rate) > 1e-9:
            logger.info(f"BABY_STEP | Interest Rate: {old_rate:.4f} -> {cb.base_rate:.4f}", **log_tag)
        
        if abs(old_val["income_tax"] - gov.income_tax_rate) > 1e-9:
            logger.info(f"BABY_STEP | Income Tax: {old_val['income_tax']:.4f} -> {gov.income_tax_rate:.4f}", **log_tag)
            
        if abs(old_val["corp_tax"] - gov.corporate_tax_rate) > 1e-9:
            logger.info(f"BABY_STEP | Corp Tax: {old_val['corp_tax']:.4f} -> {gov.corporate_tax_rate:.4f}", **log_tag)
            
        if abs(old_val["welfare"] - gov.welfare_budget_multiplier) > 1e-9:
            logger.info(f"BABY_STEP | Welfare Budget: {old_val['welfare']:.2f} -> {gov.welfare_budget_multiplier:.2f}", **log_tag)
            
        if abs(old_val["subsidy"] - gov.firm_subsidy_budget_multiplier) > 1e-9:
            logger.info(f"BABY_STEP | Firm Subsidy: {old_val['subsidy']:.2f} -> {gov.firm_subsidy_budget_multiplier:.2f}", **log_tag)
