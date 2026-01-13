from typing import Dict, Any
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.ai.enums import PoliticalParty
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
        from simulation.ai.government_ai import GovernmentAI
        self.ai = GovernmentAI(government, config_module)
        self.last_action_tick = -999

    def decide(self, government: Any, market_data: Dict[str, Any], current_tick: int) -> Dict[str, Any]:
        """
        Policy Decision Cycle.
        Enforces 30-tick (1 month) silent interval as per Architect Prime's Directive.
        """
        action_interval = getattr(self.config, "GOV_ACTION_INTERVAL", 30)
        
        # 30-tick Interval Enforcement
        if current_tick > 0 and current_tick % action_interval != 0:
            return {"policy_type": "AI_ADAPTIVE", "status": "COOLDOWN"}

        # 1. Observe and Decide (Brain)
        action = self.ai.decide_policy(market_data, current_tick)
        self.last_action_tick = current_tick

        # 2. Execution (Actuator)
        # Store old values for logging baby steps
        old_values = {
            "income_tax": government.income_tax_rate,
            "corp_tax": government.corporate_tax_rate,
            "welfare": government.welfare_budget_multiplier,
            "subsidy": government.firm_subsidy_budget_multiplier
        }
        
        # Central Bank (Rate) control
        central_bank = market_data.get("central_bank")
        old_rate = central_bank.base_rate if central_bank else 0.0

        # Constants from Architect Directive
        TAX_STEP = 0.01          # +-1.0%p
        RATE_STEP = 0.0025       # +-0.25%p
        BUDGET_STEP = 0.1        # +-10%
        
        # 3. Translation Logic (Mapping Action -> Physical Change)
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
        
        # 4. The Safety Valve (Clipping & Bounds)
        # Interest Rate [0% ~ 20%]
        if central_bank:
            central_bank.base_rate = max(0.0, min(0.20, central_bank.base_rate))
        
        # Tax Rate [5% ~ 50%]
        tax_min, tax_max = 0.05, 0.50
        government.income_tax_rate = max(tax_min, min(tax_max, government.income_tax_rate))
        government.corporate_tax_rate = max(tax_min, min(tax_max, government.corporate_tax_rate))
        
        # Budget Allocation [10% ~ 100%]
        budget_min, budget_max = 0.1, 1.0 # Min 10% for baseline survival
        government.welfare_budget_multiplier = max(budget_min, min(budget_max, government.welfare_budget_multiplier))
        government.firm_subsidy_budget_multiplier = max(budget_min, min(budget_max, government.firm_subsidy_budget_multiplier))

        # 5. Logging Baby Steps
        self._log_changes(government, old_values, central_bank, old_rate, action, current_tick)

        # 6. Reward & Learning
        reward = self._calculate_reward(government, market_data)
        self.ai.update_learning_with_state(reward, market_data)

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

    def _calculate_reward(self, government: Any, market_data: Dict[str, Any]) -> float:
        """
        While Brain (Alpha) recalculates reward internally for Q-Learning,
        we provide the baseline (Approval Rating) here for legacy metrics.
        """
        return getattr(government, "perceived_public_opinion", 0.5)
